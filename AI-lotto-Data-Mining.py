import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import io
import sqlite3
import re  # Import the re module for regular expressions
import cv2
import numpy as np
import os
import csv


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

def extract_to_csv(ocr_text, year, counter, fileName):
    
    # Define the directory where you want to save the CSV file
    directory = 'csv-files'
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    csv_filename = "initName.csv"

    if(fileName != "default"):
        fileNameModified = fileName[:-3] + "csv"
        csv_filename = os.path.join(directory, fileNameModified)
    else:
        # Construct the CSV filename with the directory
        csv_filename = os.path.join(directory, f'processed_image_{year}_{counter}.csv')

    
    # Define the regex pattern to match the date, winning combination, and drawing number
    pattern = r"(So|Mi|Fr)\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})\s+.*?\s+Zieh\.\s+(\d+)"
    
    # Open the CSV file for writing
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        # Create a CSV writer object
        csv_writer = csv.writer(csvfile)
        # Write the header row
        csv_writer.writerow(['Datum', 'LOTTO Gewinnzahlen', 'Zz', 'Zieh.'])

        # Find all matches of the pattern in the OCR text
        matches = re.findall(pattern, ocr_text, re.MULTILINE)
        
        for match in matches:
            day_of_week, date, winning_numbers, drawing_number = match
            # Remove extra spaces from the winning numbers string
            winning_numbers_clean = ' '.join(winning_numbers.split())
            # Write the extracted information to the CSV file
            csv_writer.writerow([date, winning_numbers_clean, 'Zz', drawing_number])

def save_ocr_text_as_txt(ocr_text, year, counter, fileName):
    # Define the directory where you want to save the TXT file
    directory = 'raw-ocr-reading'
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    txt_filename = "initName.txt"

    if fileName != "default":
        # Replace the original file extension with .txt
        fileNameModified = fileName[:-3] + "txt"
        txt_filename = os.path.join(directory, fileNameModified)
    else:
        # Construct the TXT filename with the directory for the default naming convention
        txt_filename = os.path.join(directory, f'processed_image_{year}_{counter}.txt')

    # Open the TXT file for writing
    with open(txt_filename, 'w', encoding='utf-8') as txtfile:
        # Write the OCR text to the file
        txtfile.write(ocr_text)

    print(f"OCR text has been saved to {txt_filename}.")

def parse_and_insert_data(conn, year, ocr_text):
    c = conn.cursor()
    
    print(ocr_text)
    
    # Adjust the regex pattern to correctly capture the groups
    pattern1 = r"(So|Mi|Fr)\s+(\d{2}\.\d{2}\.\d{4})\s+\|\s+([\d ]+)\s+(\d+)\s+Jackpot\s+([\d.,]+)\s+.*?\|\s+(\d+)"
    pattern2 = r"(So|Mi|Fr)\s+(\d{2}\.\d{2}\.\d{4})\s+\|\s+((?:\d{2}\s+){6})(\d{2})\s+.*?\|\s+(\d+)"

    pattern = r"(So|Mi|Fr)\s+(\d{2}\.\d{2}\.\d{4}).*?(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}).*?Zieh\.\s+(\d+)"
  

    matches = re.findall(pattern, ocr_text.replace('\n', ' '))
    matches2 = re.findall(pattern2, ocr_text.replace('\n', ' '))
    
    for match in matches:
        day_of_week, drawing_date, numbers_str, additional_number, jackpot, drawingNr = match
        
        # Convert drawing_date from DD.MM.YYYY to YYYY-MM-DD format
        day, month, year = drawing_date.split('.')
        iso_format_date = f"{year}-{month}-{day}"  # Convert to YYYY-MM-DD format
        
        # Split the numbers string into individual numbers, convert to integers, and remove any empty values
        numbers = [int(n) for n in numbers_str.split() if n.isdigit()]

        # Correctly parse the jackpot amount, removing spaces, commas, and periods for thousands separators
        jackpot_amount = jackpot.replace(" ", "").replace(",", "").replace(".", "")

        # Ensure the drawing date and number don't already exist
        c.execute("SELECT id FROM date_of_drawing WHERE dateDrawing = ? AND drawingNr = ?", (iso_format_date, drawingNr))
        existing_entry = c.fetchone()

        if not existing_entry:
            # Insert the new drawing date and number
            c.execute("INSERT INTO date_of_drawing (dateDrawing, drawingNr) VALUES (?, ?)", (iso_format_date, drawingNr))
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


def process_images_from_directory(conn, directory_path):
    # Get a list of file names in the specified directory
    try:
        image_files = [f for f in os.listdir(directory_path) if f.endswith(('.png'))]
    except FileNotFoundError:
        print(f"The directory {directory_path} was not found.")

        return
    
    
    counter = 1  # Initialize a counter for naming CSV files
    for image_name in image_files:
        
        # Construct the full image path
        image_path = os.path.join(directory_path, image_name)
        # Open the image file
        with Image.open(image_path) as image:
            preprocessed_image = preprocess_image(image)
            # OCR the image
            extracted_text = pytesseract.image_to_string(preprocessed_image)
            # Insert the OCR result into the database
            year = get_year_from_image_name(image_name)
            insert_ocr_result(conn, year, extracted_text)
            
            # Instead of parse_and_insert_data, directly save to CSV
            extract_to_csv(extracted_text, year, counter, image_name)
            save_ocr_text_as_txt(extracted_text, year, counter, image_name)
            
            counter += 1  # Increment the counter for each image processed
            
            # Parse the OCR text and insert parsed data into related tables
            parse_and_insert_data(conn, year, extracted_text)

def get_year_from_image_name(image_name):
    # Extract the year from the image name assuming the format is "processed_image_YEAR_NUMBER.png"
    match = re.search(r"(\d{4})", image_name)
    return int(match.group(1)) if match else None



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
        image_counter = 1  # Counter to create unique image names

        for img in images:
            img_src = img['src']
            if img_src.startswith('at_grafik/zahlenarchiv/x'):
                full_img_url = base_image_url + img_src
                img_response = requests.get(full_img_url)

                if img_response.status_code == 200:
                    # Load and preprocess the image
                    image = Image.open(io.BytesIO(img_response.content))
                    preprocessed_image = preprocess_image(image)
                    
                    # Define the base directory and image name
                    base_dir = "./pictures"  # Adjust the path as needed
                    image_name = f"processed_image_{year}_{image_counter}.png"
                    image_counter += 1
                   
                    # Save the processed image
                    save_processed_image(preprocessed_image, base_dir, image_name)
                    
                    # Apply OCR on the preprocessed image
                    extracted_text = pytesseract.image_to_string(preprocessed_image)
                    
                    # Save the raw OCR result
                    insert_ocr_result(conn, year, extracted_text)
                    
                    extract_to_csv(extracted_text, year, image_counter, "default")
                    save_ocr_text_as_txt(extracted_text, year, image_counter, "default")
                    
                    # Parse the OCR text and insert parsed data into related tables
                    parse_and_insert_data(conn, year, extracted_text)
                else:
                    print(f"Failed to download image for year {year}")
    else:
        print(f"Failed to retrieve the webpage for year {year}")


def save_processed_image(image, base_dir, image_name):
    """
    Saves the processed image to a specified directory with a given name.

    :param image: The PIL Image object to save.
    :param base_dir: The base directory where the images folder will be created.
    :param image_name: The name of the image file to save.
    """
    # Ensure the base directory exists
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # Define the full path for the image
    image_path = os.path.join(base_dir, image_name)

    # Save the image
    image.save(image_path)

def insert_ocr_result(conn, year, ocr_text):
    c = conn.cursor()
    c.execute("INSERT INTO ocr_results (year, ocr_text) VALUES (?, ?)", (year, ocr_text))
    conn.commit()

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
    print("in winning comb...")
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
    
def display_drawing_date(conn):
    print("in drawing date...")
    c = conn.cursor()
    # Query to join date_of_drawing and winningCombination tables to get March records
    query = """
    SELECT * FROM date_of_drawing
    """
    c.execute(query)
    results = c.fetchall()
    
    if results:
        print("Winning combinations:")
        for row in results:
            print(row)
    else:
        print("No winning combinations found for March.")

def debug_print_dates(conn):
    c = conn.cursor()
    c.execute("SELECT dateDrawing FROM date_of_drawing LIMIT 10")
    for row in c.fetchall():
        print(row)

def fetch_data_byURL(conn):
    print('Starting the pytesseractOCR exe...')
    
    pytesseract.pytesseract.tesseract_cmd = r'D:\TesseractOCR\tesseract.exe'
    base_url = 'https://www.6richtige.at/zahlenarchiv_at_{}.html'
    
    print('Find the base image url: ')
    base_image_url = 'https://www.6richtige.at/'
    print(base_image_url)

    start_year = 2022
    end_year = 2022


    print('Process the images for year: ' + str(start_year) + ' end year: ' + str(end_year))

    
    for year in range(start_year, end_year + 1):
        process_images_for_year(conn, year, base_url, base_image_url)
        
    
    return conn

def main():
    
    print('Initialize the database...')
    conn, _ = initialize_database()
    
    # Ask the user if they want to fetch new data
    fetch_data = input("Do you want to fetch new data? (y/n): ").strip().lower()
    
    if fetch_data == 'y':
        conn = fetch_data_byURL(conn)
    else:
        process_images_from_directory(conn, './pictures')
        
        
    #display_winning_combinations_for_march(conn)

    #display_winning_comb(conn)
    
    #display_drawing_date(conn)

    #debug_print_dates(conn)

    # TODO: OCR_text doesnt recognize 1 - writes either 3 or 4 instead.
    # TODO: Rerun the queries and check the db if it has all the correct data. 

    conn.close()


if __name__ == '__main__':
    main()
