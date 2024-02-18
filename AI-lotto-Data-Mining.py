import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import pytesseract
import io
import sqlite3
import re  # Import the re module for regular expressions


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
    """
    Parses the OCR text for dates, winning numbers, and additional information,
    then inserts them into the respective tables.
    """
    c = conn.cursor()

    # Regular expression to match the pattern in the provided example
    pattern = r"(So|Mi) (\d{2}\.\d{2}\.\d{4}) \| ([\d ]+) (\d{2}) Jackpot ([\d ,.]+)"
    matches = re.findall(pattern, ocr_text.replace('\n', ' '))

    for match in matches:
        # Extracting data from each match
        drawing_date, numbers_str, additional_number, jackpot = match[1], match[2], match[3], match[4]

        # Splitting the numbers and converting them to integers
        numbers = [int(n) for n in numbers_str.split()]

        # Insert into date_of_drawing
        c.execute("INSERT INTO date_of_drawing (dateDrawing, drawingNr) VALUES (?, ?)", (drawing_date, 1))
        date_id = c.lastrowid

        # Assuming n1 to n6 are the main numbers and 'additional_number' is the extra number
        if len(numbers) == 6:
            n1, n2, n3, n4, n5, n6 = numbers
            c.execute('''
            INSERT INTO winningCombination 
            (n1, n2, n3, n4, n5, n6, additional_number, date_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (n1, n2, n3, n4, n5, n6, additional_number, date_id))

        # Insert into jocker table if needed
        # Example: Assuming 'winningCombination' is a placeholder for jocker-related data
        # You might need to adjust this part according to your actual schema and data
        jocker_number = "Placeholder"  # Replace or remove based on actual use-case
        c.execute("INSERT INTO jocker (winningCombination, date_id) VALUES (?, ?)", (jocker_number, date_id))

    conn.commit()

def insert_ocr_result(conn, year, ocr_text):
    c = conn.cursor()
    c.execute("INSERT INTO ocr_results (year, ocr_text) VALUES (?, ?)", (year, ocr_text))
    conn.commit()

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
                    image = Image.open(io.BytesIO(img_response.content))
                    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
                    image = image.convert("L")
                    extracted_text = pytesseract.image_to_string(image)
                    
                    # Save the raw OCR result
                    insert_ocr_result(conn, year, extracted_text)
                    
                    # Parse the OCR text and insert parsed data into related tables
                    parse_and_insert_data(conn, year, extracted_text)

                    print(f"Year {year}: {extracted_text}")
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

# Usage example:
# conn = sqlite3.connect('lottery_ocr_results.db')
# display_winning_combinations_for_march(conn)
# conn.close()



def main():
    pytesseract.pytesseract.tesseract_cmd = r'D:\TesseractOCR\tesseract.exe'
    base_url = 'https://www.6richtige.at/zahlenarchiv_at_{}.html'
    base_image_url = 'https://www.6richtige.at/'

    start_year = 2022
    end_year = 2022

    conn, _ = initialize_database()

    for year in range(start_year, end_year + 1):
        process_images_for_year(conn, year, base_url, base_image_url)

    conn.close()

if __name__ == '__main__':
    main()
