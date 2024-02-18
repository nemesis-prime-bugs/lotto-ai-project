# lotto-ai-project

## Intro
This Python script is designed to scrape lottery drawing information from a specific website, use Optical Character Recognition (OCR) to extract text from images, parse the extracted text for specific data (such as winning numbers and drawing dates), and then store this data in a structured SQLite database. It also includes functionality to query and display the winning combinations for a specified month (March in the example). Below is an explanation of each part of the code:

### Import Statements

```python
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import pytesseract
import io
import sqlite3
import re
```

- `requests`: Library for making HTTP requests in Python.
- `BeautifulSoup`: Library for parsing HTML and XML documents. It's used here to scrape and process web content.
- `PIL (Python Imaging Library)`, specifically `Image` and `ImageOps`: Used for image processing tasks such as opening, resizing, and converting images to grayscale.
- `pytesseract`: Python wrapper for Google's Tesseract-OCR Engine. It's used to extract text from images.
- `io`: Provides the capability to handle various types of I/O (Input/Output). Here, it's used for handling in-memory binary streams (images in this case).
- `sqlite3`: Built-in library for SQLite database management. It's used to store and query the extracted data.
- `re`: Module for working with regular expressions, used here for parsing the OCR text.

### Database Initialization

```python
def initialize_database():
    ...
```

Initializes the SQLite database by connecting to it and creating the necessary tables if they don't already exist. Tables include `ocr_results` for storing raw OCR text, `date_of_drawing` for drawing dates, `winningCombination` for storing the winning numbers, and `jocker` for joker numbers or other specific lottery information.

### Parsing and Data Insertion

```python
def parse_and_insert_data(conn, year, ocr_text):
    ...
```

Parses the OCR text extracted from the lottery images to find dates, winning numbers, and other relevant information. Then, it inserts this parsed data into the corresponding tables in the SQLite database.

### OCR Result Insertion

```python
def insert_ocr_result(conn, year, ocr_text):
    ...
```

Inserts the raw OCR text along with the year into the `ocr_results` table. This function is called immediately after the OCR text is extracted from an image.

### Image Processing for a Year

```python
def process_images_for_year(conn, year, base_url, base_image_url):
    ...
```

Processes images for a specific year by scraping the website for image URLs, downloading the images, performing OCR to extract text, and then saving both the raw OCR results and the parsed data into the database.

### Display Winning Combinations for March

```python
def display_winning_combinations_for_march(conn):
    ...
```

Queries the database for winning combinations in March, joining the `date_of_drawing` and `winningCombination` tables. It displays the date, winning numbers, and additional numbers for each relevant drawing.

### Main Function

```python
def main():
    ...
```

The entry point of the script. It sets up the Tesseract command path (necessary for pytesseract to interface with the Tesseract-OCR engine), initializes the database, processes images for the specified year(s), and finally closes the database connection.

### Running the Script

```python
if __name__ == '__main__':
    main()
```

A Python best practice that checks if the script is executed as the main program and runs the `main` function if it is. This prevents `main()` from executing when the script is imported as a module in another script.

### Overall Functionality

The script automates the process of extracting lottery drawing information from images, parsing this information, and storing it in a structured format for easy querying and analysis. This can be particularly useful for tracking drawing results over time, analyzing patterns, or simply archiving the data.