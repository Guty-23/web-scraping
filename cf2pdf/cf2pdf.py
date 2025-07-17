import sys, os, io
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc  # pip install undetected-chromedriver
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PyPDF2 import PageObject
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from typing import List, Tuple, Dict, Optional
from urllib.error import URLError
try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF (fitz) is required. Install with 'pip install pymupdf'.")
try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow is required. Install with 'pip install pillow'.")

# =====================
# Configuration
# =====================
CONTEST_FILE = 'contest.txt'
WAIT_TIME_MIN = 10
WAIT_TIME_MAX = 20
PDF_PAGE_WIDTH = 612
PDF_PAGE_HEIGHT = 792
LOG_LEVEL = logging.INFO

# Crop/trim box constants for PDF pages
TRIM_LOWER_LEFT = (0, 0)
TRIM_UPPER_RIGHT_FIRST = (406, 730)
TRIM_UPPER_RIGHT_OTHER = (406, 842)
CROP_LOWER_LEFT = (0, 0)
CROP_UPPER_RIGHT_FIRST = (406, 730)
CROP_UPPER_RIGHT_OTHER = (406, 842)

logging.basicConfig(level=LOG_LEVEL, format='%(levelname)s: %(message)s')

##################################################################################
# To use the script, fill a line in "contest.txt" for each problem that you want. #
# The FIRST line of "contest.txt" should be the contest name (used for the output PDF). #
# Each subsequent line should have four values (separated by a space):           #
#                                                                                #
# CONTEST_ID PROBLEM_ID LETTER_YOUR_PROBLEM_SET PROBLEM_TITLE (Optional:GYM)     #
#                                                                                #
# NOTE: If there are spaces in the title, use underscore ("_") in "contest.txt",  #
# blank spaces will be used in the .pdf. Also, there should be no extra lines.    #
#                                                                                #
# TO DO:                                                                         #
#   - Center title                                                               #
#   - Erase auxiliary files generated                                            #
#   - Avoid hardcoding constants                                                 #
#                                                                                #
#  Requirements:                                                                 #
#    - pip3 install selenium webdriver-manager beautifulsoup4 reportlab PyPDF2<3.0 #
#    - Also need Chrome browser installed on the system                          #
##################################################################################

def parse_contest_file(filename: str) -> Tuple[str, List[Dict]]:
    """Parse contest.txt and return contest name and a list of problem entries."""
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    if not lines:
        raise ValueError('contest.txt is empty!')
    contest_name = lines[0]
    problems = []
    for line in lines[1:]:
        input_line = line.split()
        gym = False
        if input_line[-1].upper() == 'GYM':
            contest_id, problem_index, letter, title, _ = input_line
            gym = True
        else:
            contest_id, problem_index, letter, title = input_line
        problems.append({
            'contest_id': contest_id,
            'problem_index': problem_index,
            'letter': letter,
            'title': title.replace('_', ' '),
            'gym': gym
        })
    return contest_name, problems

def create_pdf_merger(letters: List[str]) -> PdfFileMerger:
    """Create a PdfFileMerger from a list of letter filenames."""
    pdf_merger = PdfFileMerger()
    for letter in sorted(letters):
        pdf_merger.append(os.path.join(os.getcwd(), f'{letter}.pdf'))
    return pdf_merger

def process_problem(problem: Dict) -> Optional[str]:
    """Download, crop, and return the letter for a problem, or None if failed."""
    file_name = download_from_url(problem['contest_id'], problem['problem_index'], problem['gym'])
    if file_name:
        crop_pdf(file_name, problem['letter'], problem['title'])
        return problem['letter']
    else:
        logging.warning(f"Skipping problem {problem['contest_id']}/{problem['problem_index']} due to download failure")
        return None

def add_letter_and_title(page: PageObject, problem_letter: str, problem_title: str) -> None:
    """Overlay the letter image and title onto the PDF page."""
    imgTemp = io.BytesIO()
    imgTempWHITE = io.BytesIO()
    imgDoc = canvas.Canvas(imgTemp)
    imgDocWHITE = canvas.Canvas(imgTempWHITE)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont('Helvetica-Bold', 20 if len(problem_title) < 17 else 14)
    can.drawString(200 - int((4.1 if len(problem_title) < 17 else 2.4) * len(problem_title)), 705, problem_title)
    can.showPage()
    can.save()
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    imgPath = os.path.join(os.getcwd(), 'letters', f'{problem_letter}.png')
    imgPathWHITE = os.path.join(os.getcwd(), 'letters', 'BLANCO_LARGO.png')
    imgDoc.drawImage(imgPath, 10, 645, 96, 96)
    imgDocWHITE.drawImage(imgPathWHITE, 106, 635, 300, 300)
    imgDoc.save()
    imgDocWHITE.save()
    overlay = PdfFileReader(io.BytesIO(imgTemp.getvalue())).getPage(0)
    overlayWHITE = PdfFileReader(io.BytesIO(imgTempWHITE.getvalue())).getPage(0)
    page.mergePage(overlayWHITE)
    page.mergePage(overlay)
    page.mergePage(new_pdf.getPage(0))

def print_page_to_pdf(driver, filename: str) -> None:
    """Use Chrome DevTools Protocol to print the page to PDF."""
    pdf = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "landscape": False
    })
    import base64
    with open(filename, "wb") as f:
        f.write(base64.b64decode(pdf['data']))

def get_problem_content(contest_id: str, problem_index: str, gym: bool = False, return_driver: bool = False):
    """Load the problem page with Selenium and return the driver object or page source."""
    logging.info(f"Fetching problem {contest_id}/{problem_index} via Selenium...")
    problem_url = f'https://codeforces.com/problemset/problem/{contest_id}/{problem_index}'
    if gym:
        problem_url = f'https://codeforces.com/gym/{contest_id}/problem/{problem_index}'
    logging.info(f"URL: {problem_url}")
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    with uc.Chrome(options=chrome_options, use_subprocess=True) as driver:
        driver.get(problem_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        wait_time = random.randint(WAIT_TIME_MIN, WAIT_TIME_MAX)
        logging.info(f"Waiting {wait_time} seconds for Cloudflare verification...")
        time.sleep(wait_time)
        if return_driver:
            return driver
        else:
            content = driver.page_source
            return content

def fallback_html_to_pdf(html_content: str, filename: str) -> None:
    """Fallback: convert HTML content to a simple PDF using reportlab."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text()
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    paragraphs = text_content.split('\n\n')
    for para in paragraphs:
        para = para.strip()
        if para:
            story.append(Paragraph(para, normal_style))
            story.append(Spacer(1, 6))
    doc.build(story)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 5  # seconds

def download_from_url(contest_id: str, problem_index: str, gym: bool) -> Optional[str]:
    """Download the problem page and save as PDF, using fallback if needed. Retries on network errors."""
    file_name = f'{contest_id}-{problem_index}.pdf'
    if os.path.isfile(file_name):
        logging.info(f"PDF already exists for {contest_id}/{problem_index}: {file_name}")
        return file_name
    attempt = 0
    retryable_errors = [
        'Temporary failure in name resolution',
        'urlopen error',
        'net::ERR_CONNECTION_CLOSED',
        'net::ERR_CONNECTION_RESET',
        'net::ERR_TIMED_OUT',
        'net::ERR_INTERNET_DISCONNECTED',
        'net::ERR_NETWORK_CHANGED',
        'net::ERR_PROXY_CONNECTION_FAILED',
        'net::ERR_NAME_NOT_RESOLVED',
        'net::ERR_CONNECTION_REFUSED',
    ]
    while attempt < MAX_RETRIES:
        try:
            driver = get_problem_content(contest_id, problem_index, gym, return_driver=True)
            if driver and hasattr(driver, 'page_source'):
                try:
                    print_page_to_pdf(driver, file_name)
                    logging.info(f"Successfully created PDF: {file_name}")
                except Exception as e:
                    logging.error(f"Error printing to PDF: {e}")
                    html_content = driver.page_source
                    fallback_html_to_pdf(html_content, file_name)
                finally:
                    if driver is not None and not isinstance(driver, str) and hasattr(driver, 'quit'):
                        driver.quit()
                return file_name
            else:
                logging.warning(f"Failed to download content for {contest_id}/{problem_index}")
                return None
        except (URLError, Exception) as e:
            error_str = str(e)
            if any(err in error_str for err in retryable_errors) or isinstance(e, URLError):
                attempt += 1
                if attempt < MAX_RETRIES:
                    wait_time = RETRY_BACKOFF_BASE * attempt
                    logging.warning(f"Network error on {contest_id}/{problem_index}: {e}. Retrying in {wait_time} seconds (attempt {attempt}/{MAX_RETRIES})...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Max retries reached for {contest_id}/{problem_index}. Skipping.")
                    return None
            else:
                logging.error(f"Non-network error for {contest_id}/{problem_index}: {e}")
                return None
    return None

def add_white_block_on_last_page(pdf_path: str, blanco_path: str = os.path.join(os.getcwd(), 'letters', 'BLANCO_LARGO.png')):
    """Post-process the PDF: overlay a white block on the last page at the copyright string's Y position. If not found, delete last page and repeat."""
    doc = fitz.open(pdf_path)
    while doc.page_count > 1:
        last_page = doc[-1]
        text_instances = last_page.search_for("Codeforces (c) Copyright")
        if not text_instances:
            # Fallback: try just 'Copyright'
            text_instances = last_page.search_for("Copyright")
        if text_instances:
            # Found copyright, overlay white block
            rect = text_instances[0]
            y = rect.y0
            img = Image.open(blanco_path)
            img_width, img_height = img.size
            page_width = last_page.rect.width
            scale = page_width / img_width
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            temp_img_path = "_temp_blanco_resized.png"
            img.save(temp_img_path)
            last_page.insert_image(
                fitz.Rect(0, y, page_width, y + new_height),
                filename=temp_img_path,
                overlay=True
            )
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()
            os.remove(temp_img_path)
            return
        else:
            # Delete last page and continue
            doc.delete_page(doc.page_count - 1)
    # If only one page left, check it one last time
    last_page = doc[-1]
    text_instances = last_page.search_for("Codeforces (c) Copyright")
    if not text_instances:
        text_instances = last_page.search_for("Copyright")
    if text_instances:
        rect = text_instances[0]
        y = rect.y0
        img = Image.open(blanco_path)
        img_width, img_height = img.size
        page_width = last_page.rect.width
        scale = page_width / img_width
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        temp_img_path = "_temp_blanco_resized.png"
        img.save(temp_img_path)
        last_page.insert_image(
            fitz.Rect(0, y, page_width, y + new_height),
            filename=temp_img_path,
            overlay=True
        )
        doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()
        os.remove(temp_img_path)
    else:
        print(f"No copyright string found in any last page of {pdf_path}")
        doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()

def crop_pdf(file_name: str, letter: str, title: str) -> None:
    """Crop the PDF and add letter/title overlays."""
    with open(file_name, "rb") as input_pdf_problem:
        input_pdf = PdfFileReader(input_pdf_problem)
        output_pdf = PdfFileWriter()
        default_box_page = {
            0: {
                'trimLowerLeft': TRIM_LOWER_LEFT,
                'trimUpperRight': TRIM_UPPER_RIGHT_FIRST,
                'cropLowerLeft': CROP_LOWER_LEFT,
                'cropUpperRight': CROP_UPPER_RIGHT_FIRST
            },
            1: {
                'trimLowerLeft': TRIM_LOWER_LEFT,
                'trimUpperRight': TRIM_UPPER_RIGHT_OTHER,
                'cropLowerLeft': CROP_LOWER_LEFT,
                'cropUpperRight': CROP_UPPER_RIGHT_OTHER
            }
        }
        for i in range(input_pdf.getNumPages()):
            page = input_pdf.getPage(i)
            width = float(page.mediaBox.getUpperRight_x())
            height = float(page.mediaBox.getUpperRight_y())
            logging.info(f"page {i+1} : Width x Height  = {width} x {height}")
            # Rescale if not 612x792
            if width != PDF_PAGE_WIDTH or height != PDF_PAGE_HEIGHT:
                scale_x = PDF_PAGE_WIDTH / width
                scale_y = PDF_PAGE_HEIGHT / height
                scale = min(scale_x, scale_y)
                new_page = PageObject.createBlankPage(None, PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT)
                new_page.mergeScaledTranslatedPage(page, scale, 0, 0)
                page = new_page
                width = PDF_PAGE_WIDTH
                height = PDF_PAGE_HEIGHT
            box = default_box_page[int(i > 0)]
            page.trimBox.lowerLeft = (Decimal(box['trimLowerLeft'][0]), Decimal(box['trimLowerLeft'][1]))
            page.trimBox.upperRight = (Decimal(box['trimUpperRight'][0]), Decimal(box['trimUpperRight'][1]))
            page.cropBox.lowerLeft = (Decimal(box['cropLowerLeft'][0]), Decimal(box['cropLowerLeft'][1]))
            page.cropBox.upperRight = (Decimal(box['cropUpperRight'][0]), Decimal(box['cropUpperRight'][1]))
            if i == 0:
                add_letter_and_title(page, letter, title)
            output_pdf.addPage(page)
        with open(f'{letter}.pdf', "wb") as output_file:
            output_pdf.write(output_file)
    # Post-process: add white block on last page
    add_white_block_on_last_page(f'{letter}.pdf')

def main() -> None:
    """Main entry point: parse contest file, process problems, and merge PDFs."""
    try:
        contest, problems = parse_contest_file(CONTEST_FILE)
        letters = []
        for problem in problems:
            letter = process_problem(problem)
            if letter:
                letters.append(letter)
        pdf_merger = create_pdf_merger(letters)
        with open(f'{contest}.pdf', 'wb') as output_file:
            pdf_merger.write(output_file)
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == '__main__':
    main()
 

