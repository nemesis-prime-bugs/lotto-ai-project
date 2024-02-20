import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import io
import sqlite3
import re  # Import the re module for regular expressions
import cv2
import numpy as np


# Create Db Schema...
def initialize_database():
    conn = sqlite3.connect('lottery_ocr_results.db')
    c = conn.cursor()
    # Create tables
    c.execute('''
    CREATE TABLE IF NOT EXISTS ocr_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER,
        ocr_text TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS date_of_drawing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateDrawing TEXT,
        drawingNr INTEGER
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS winningCombination (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        n1 INTEGER,
        n2 INTEGER,
        n3 INTEGER,
        n4 INTEGER,
        n5 INTEGER,
        n6 INTEGER,
        additional_number INTEGER,
        jocker_id INTEGER,
        date_id INTEGER,
        FOREIGN KEY(jocker_id) REFERENCES jocker(id),
        FOREIGN KEY(date_id) REFERENCES date_of_drawing(id)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS jocker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        winningCombination TEXT,
        date_id INTEGER,
        FOREIGN KEY(date_id) REFERENCES date_of_drawing(id)
    )
    ''')
    conn.commit()
    return conn, c

def parse_and_insert_data(conn, year, ocr_text):
    c = conn.cursor()
    
    # Adjust the regex pattern to correctly capture the groups
    pattern = r"(So|Mi)\s+(\d{2}\.\d{2}\.\d{4})\s+\|\s+([\d ]+)\s+(\d+)\s+Jackpot\s+([\d.,]+)\s+.*?\|\s+(\d+)"
    pattern2 = r"(So|Mi|Fr)\s+(\d{2}\.\d{2}\.\d{4})\s+\|\s+((?:\d{2}\s+){6})(\d{2})\s+.*?\|\s+(\d+)"

    matches = re.findall(pattern, ocr_text.replace('\n', ' '))
    matches2 = re.findall(pattern2, ocr_text.replace('\n', ' '))

    for match in matches:
        day_of_week, drawing_date, numbers_str, additional_number, jackpot, drawingNr = match

        # Split the numbers string into individual numbers, convert to integers, and remove any empty values
        numbers = [int(n) for n in numbers_str.split() if n.isdigit()]

        # Correctly parse the jackpot amount, removing spaces, commas, and periods for thousands separators
        jackpot_amount = jackpot.replace(" ", "").replace(",", "").replace(".", "")

        # Ensure the drawing date and number don't already exist
        c.execute("SELECT id FROM date_of_drawing WHERE dateDrawing = ? AND drawingNr = ?", (drawing_date, drawingNr))
        existing_entry = c.fetchone()

        if not existing_entry:
            # Insert the new drawing date and number
            c.execute("INSERT INTO date_of_drawing (dateDrawing, drawingNr) VALUES (?, ?)", (drawing_date, drawingNr))
            date_id = c.lastrowid

            # Insert the winning numbers, making sure to separate the main numbers from the additional number
            if len(numbers) == 6:
                n1, n2, n3, n4, n5, n6 = numbers
                additional_number = int(additional_number)
                c.execute('''
                INSERT INTO winningCombination
                (n1, n2, n3, n4, n5, n6, additional_number, date_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (n1, n2, n3, n4, n5, n6, additional_number, date_id))
            else:
                print(f"Error: Incorrect number of winning numbers for entry dated {drawing_date}.")

            # Insert into the jocker table, if applicable
            c.execute("INSERT INTO jocker (winningCombination, date_id) VALUES (?, ?)", (jackpot_amount, date_id))
        else:
            print(f"Skipping existing entry for {drawing_date} with drawing number {drawingNr}.")

    conn.commit()


def insert_ocr_result(conn, year, ocr_text):
    c = conn.cursor()
    c.execute("INSERT INTO ocr_results (year, ocr_text) VALUES (?, ?)", (year, ocr_text))
    conn.commit()


def preprocess_image(image):
    """
    Apply preprocessing steps to enhance the image for OCR.
    """
    # Convert to grayscale
    image = image.convert("L")
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Factor may need adjustment
    
    # Convert PIL Image to OpenCV format for advanced preprocessing
    open_cv_image = np.array(image) 
    # Apply denoising - consider this step optional as it's quite advanced
    # open_cv_image = cv2.fastNlMeansDenoising(open_cv_image, None, 30, 7, 21)
    
    # Thresholding/Binarization
    _, open_cv_image = cv2.threshold(open_cv_image, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Convert back to PIL Image
    image = Image.fromarray(open_cv_image)
    
    # Resizing (if not already done)
    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    
    return image

def process_images_for_year(conn, year, base_url, base_image_url):
    url = base_url.format(year)
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all('img')

        for img in images:
            img_src = img['src']
            if img_src.startswith('at_grafik/zahlenarchiv/x'):
                full_img_url = base_image_url + img_src
                img_response = requests.get(full_img_url)

                if img_response.status_code == 200:
                    # Load and preprocess the image
                    image = Image.open(io.BytesIO(img_response.content))
                    preprocessed_image = preprocess_image(image)
                    
                    # Apply OCR on the preprocessed image
                    extracted_text = pytesseract.image_to_string(preprocessed_image)
                    
                    # Save the raw OCR result
                    insert_ocr_result(conn, year, extracted_text)
                    
                    # Parse the OCR text and insert parsed data into related tables
                    parse_and_insert_data(conn, year, extracted_text)
                else:
                    print(f"Failed to download image for year {year}")
    else:
        print(f"Failed to retrieve the webpage for year {year}")


# QUERY THE DB
def display_winning_combinations_for_march(conn):
    c = conn.cursor()
    # Query to join date_of_drawing and winningCombination tables to get March records
    query = """
    SELECT d.dateDrawing, w.n1, w.n2, w.n3, w.n4, w.n5, w.n6, w.additional_number
    FROM winningCombination w
    JOIN date_of_drawing d ON w.date_id = d.id
    WHERE strftime('%m', d.dateDrawing) = '03'
    ORDER BY d.dateDrawing ASC
    """
    c.execute(query)
    results = c.fetchall()
    
    if results:
        print("Winning combinations for March:")
        for row in results:
            date, n1, n2, n3, n4, n5, n6, additional_number = row
            print(f"Date: {date}, Numbers: {n1}, {n2}, {n3}, {n4}, {n5}, {n6}, Additional: {additional_number}")
    else:
        print("No winning combinations found for March.")

def display_winning_comb(conn):
    print("in display...")
    c = conn.cursor()
    # Query to join date_of_drawing and winningCombination tables to get March records
    query = """
    SELECT * FROM winningCombination
    """
    c.execute(query)
    results = c.fetchall()
    
    if results:
        print("Winning combinations:")
        for row in results:
            print(row)
    else:
        print("No winning combinations found for March.")
    


def main():
    pytesseract.pytesseract.tesseract_cmd = r'D:\TesseractOCR\tesseract.exe'
    base_url = 'https://www.6richtige.at/zahlenarchiv_at_{}.html'
    base_image_url = 'https://www.6richtige.at/'

    start_year = 2022
    end_year = 2022

    conn, _ = initialize_database()

    for year in range(start_year, end_year + 1):
        process_images_for_year(conn, year, base_url, base_image_url)

    display_winning_combinations_for_march(conn)

    display_winning_comb(conn)

    conn.close()


if __name__ == '__main__':
    main()
