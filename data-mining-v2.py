import sqlite3
import logging

# Enhanced logging configuration
logging.basicConfig(
    filename="lotto_processing.log",  # Save log in the current working directory
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def initialize_database():
    """Initializes the database and creates necessary tables."""
    conn = sqlite3.connect("/mnt/data/lottery_ocr_results.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotto_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            n1 INTEGER,
            n2 INTEGER,
            n3 INTEGER,
            n4 INTEGER,
            n5 INTEGER,
            n6 INTEGER,
            additional_number INTEGER,
            jackpot INTEGER
        )
    ''')
    conn.commit()
    return conn

def insert_parsed_data(conn, parsed_data):
    """
    Inserts parsed lotto results into the database.
    """
    cursor = conn.cursor()
    for result in parsed_data:
        try:
            cursor.execute('''
                INSERT INTO lotto_results (date, n1, n2, n3, n4, n5, n6, additional_number, jackpot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result["date"],
                result["numbers"][0],
                result["numbers"][1],
                result["numbers"][2],
                result["numbers"][3],
                result["numbers"][4],
                result["numbers"][5],
                result["additional_number"],
                result["jackpot"]
            ))
            logging.info(f"Inserted data for {result['date']} into the database.")
        except Exception as e:
            logging.error(f"Error inserting data for {result['date']}: {e}")
    conn.commit()

# Initialize database and process all images
conn = initialize_database()

for image_file in image_files:
    image_path = os.path.join(pictures_folder, image_file)
    image = Image.open(image_path)
    ocr_text = pytesseract.image_to_string(image)
    cleaned_text = clean_ocr_text(ocr_text)
    parsed_results = parse_lotto_results(cleaned_text)
    insert_parsed_data(conn, parsed_results)

# Finalize and close the database connection
conn.close()

# Log completion
logging.info("Processing of all images is complete.")
