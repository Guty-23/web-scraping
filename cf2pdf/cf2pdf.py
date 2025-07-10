import sys, os, io
import requests
from bs4 import BeautifulSoup, Tag
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

##################################################################################
# To use the script fill a line in "contest.txt" for each problem that you want. # 
# Each line should have four values (separated by a space):                    #
#                                                                              #    
# CONTEST_ID PROBLEM_ID LETTER_YOUR_PROBLEM_SET PROBLEM_TITLE (Optional:GYM)   #
#                                                                              #
# NOTE: If there are spaces in the title, use underscore ("_") in "contest.txt", #
# blank spaces will be used in the .pdf. Also, there should be no extra lines.  #
#                                                                               #
# TO DO:                                                                        #
#   - Center title                                                              #    
#   - Erase auxiliary files generated                                           #
#   - Avoid hardcoding constants                                                #    
#                                                                               #
#  Requirements:                                                                #        
#    - pip3 install selenium webdriver-manager beautifulsoup4 reportlab PyPDF2<3.0 #
#    - Also need Chrome browser installed on the system                         #
##################################################################################

def add_letter_and_title(page, problem_letter, problem_title):
    imgTemp = io.BytesIO()
    imgTempWHITE = io.BytesIO()
    imgDoc = canvas.Canvas(imgTemp)
    imgDocWHITE = canvas.Canvas(imgTempWHITE)
    packet = io.BytesIO()
    
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont('Helvetica-Bold', 20 if len(problem_title) < 17 else 14)
    can.drawString(200 - int( (4.1 if len(problem_title) < 17 else 2.4) *len(problem_title)), 705, problem_title)
    can.showPage()
    can.save()
    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    imgPath = os.getcwd() + '/letters/' + problem_letter + '.png'
    imgPathWHITE = os.getcwd() + '/letters/' + 'BLANCO_LARGO.png'
    imgDoc.drawImage(imgPath, 10, 645, 96, 96)
    imgDocWHITE.drawImage(imgPathWHITE, 106, 635, 300, 300)
    imgDoc.save()
    imgDocWHITE.save()

    overlay = PdfFileReader(io.BytesIO(imgTemp.getvalue())).getPage(0)
    overlayWHITE = PdfFileReader(io.BytesIO(imgTempWHITE.getvalue())).getPage(0)
    page.mergePage(overlayWHITE)
    page.mergePage(overlay)
    page.mergePage(new_pdf.getPage(0))

def print_page_to_pdf(driver, filename):
    # Use Chrome DevTools Protocol to print the page to PDF
    pdf = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "landscape": False
    })
    import base64
    with open(filename, "wb") as f:
        f.write(base64.b64decode(pdf['data']))

def get_problem_content(contest_id, problem_index, gym=False, return_driver=False):
    """Load the problem page with Selenium and return the driver object."""
    print(f"Fetching problem {contest_id}/{problem_index} via Selenium...")
    problem_url = f'https://codeforces.com/problemset/problem/{contest_id}/{problem_index}'
    if gym:
        problem_url = f'https://codeforces.com/gym/{contest_id}/problem/{problem_index}'
    print(f"URL: {problem_url}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(problem_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Refresh the page and wait for it to load completely
        driver.refresh()
        time.sleep(3)  # Wait 3 seconds for the page to fully load after refresh
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        if return_driver:
            return driver
        else:
            content = driver.page_source
            driver.quit()
            return content
    except Exception as e:
        print(f"Error fetching problem: {e}")
        if driver:
            driver.quit()
        return None

def fallback_html_to_pdf(html_content, filename):
    from bs4 import BeautifulSoup
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

def download_from_url(contest_id, problem_index, gym):
    file_name = contest_id + '-' + problem_index + '.pdf'
    if not os.path.isfile(file_name):
        driver = get_problem_content(contest_id, problem_index, gym, return_driver=True)
        if driver:
            try:
                print_page_to_pdf(driver, file_name)
                print(f"Successfully created PDF: {file_name}")
            except Exception as e:
                print(f"Error printing to PDF: {e}")
                # fallback: try to get HTML and use fallback
                html_content = driver.page_source
                fallback_html_to_pdf(html_content, file_name)
            finally:
                driver.quit()
        else:
            print(f"Failed to download content for {contest_id}/{problem_index}")
            return None
    return file_name

def crop_pdf(file_name, letter, title):
    with open(file_name, "rb") as input_pdf_problem:
        input_pdf = PdfFileReader(input_pdf_problem)
        output_pdf = PdfFileWriter()
        default_box_page = {0:{'trimLowerLeft':(0,0),'trimUpperRight':(406,730), 'cropLowerLeft':(0,0), 'cropUpperRight':(406,730)}, 
                            1:{'trimLowerLeft':(0,0),'trimUpperRight':(406,842), 'cropLowerLeft':(0,0), 'cropUpperRight':(406,842)}} 
        for i in range(input_pdf.getNumPages()):
            page = input_pdf.getPage(i)
            print("pagina",i+1,":","Ancho x Alto  =", page.mediaBox.getUpperRight_x(),"x", page.mediaBox.getUpperRight_y())
            page.trimBox.lowerLeft = (Decimal(default_box_page[int(i > 0)]['trimLowerLeft'][0]), Decimal(default_box_page[int(i > 0)]['trimLowerLeft'][1]))
            page.trimBox.upperRight = (Decimal(default_box_page[int(i > 0)]['trimUpperRight'][0]), Decimal(default_box_page[int(i > 0)]['trimUpperRight'][1]))
            page.cropBox.lowerLeft = (Decimal(default_box_page[int(i > 0)]['cropLowerLeft'][0]), Decimal(default_box_page[int(i > 0)]['cropLowerLeft'][1]))
            page.cropBox.upperRight = (Decimal(default_box_page[int(i > 0)]['cropUpperRight'][0]), Decimal(default_box_page[int(i > 0)]['cropUpperRight'][1]))
            if (i == 0):
                add_letter_and_title(page, letter, title)
            output_pdf.addPage(page)
        with open(letter + '.pdf', "wb") as output_file:
            output_pdf.write(output_file)

def main():
    letters = []
    contest = input('Ingrese el nombre del contest y no olvide completar "contest.txt" como se indica:\n\n')
    with open('contest.txt','r') as input_file:
        for line in input_file:
            input_line = line.split()
            gym = 'NO_GYM'
            if input_line[-1].upper() == 'GYM':
                contest_id,problem_index,letter,title,gym = input_line
            else:
                contest_id,problem_index,letter,title = input_line
            file_name = download_from_url(contest_id,problem_index, gym.upper() == 'GYM')
            if file_name:
                crop_pdf(file_name,letter,title.replace('_',' '))
                letters.append(letter)
            else:
                print(f"Skipping problem {contest_id}/{problem_index} due to download failure")
    pdf_merger = PdfFileMerger()
    for letter in sorted(letters):
        pdf_merger.append(os.getcwd() + '/' + letter + '.pdf')
    with open(contest + '.pdf', 'wb') as output_file:
        pdf_merger.write(output_file)
            
if __name__ == '__main__':
    main()
 

