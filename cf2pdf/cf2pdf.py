import sys, pdfkit, os, io
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

##################################################################################
# To use the script fill a line in "contest.txt" for each problem that you want. # 
# Each line should have four values (separated by a space):						 #
# 					 															 #	
# CONTEST_ID PROBLEM_ID LETTER_YOUR_PROBLEM_SET PROBLEM_TITLE                    #
#																				 #
# NOTE: If there are spaces in the title, use underscore ("_") in "contest.txt", #
# blank spaces will be used in the .pdf.										 #
#																			     #
#																				 #
# TO DO:															             #
#	- Center title																 #	
#	- Erase auxiliary files generated											 #
#	- Avoid hardcoding constants		 										 #
##################################################################################


def add_letter_and_title(page, problem_letter, problem_title):
	imgTemp = io.BytesIO()
	imgTempWHITE = io.BytesIO()
	imgDoc = canvas.Canvas(imgTemp)
	imgDocWHITE = canvas.Canvas(imgTempWHITE)
	packet = io.BytesIO()
	
	can = canvas.Canvas(packet, pagesize=letter)
	can.setFont('Helvetica-Bold', 20)
	can.drawString(150 - len(problem_title), 660, problem_title)
	can.showPage()
	can.save()
	packet.seek(0)
	new_pdf = PdfFileReader(packet)

	imgPath = os.getcwd() + '/letters/' + problem_letter + '.png'
	imgPathWHITE = os.getcwd() + '/letters/' + 'BLANCO_LARGO.png'
	imgDoc.drawImage(imgPath, 10, 600, 96, 96)    ## at (10,600) with size 96x96 (lower left is the origin )
	imgDocWHITE.drawImage(imgPathWHITE, 125, 660, 300, 300)   
	imgDoc.save()
	imgDocWHITE.save()

	overlay = PdfFileReader(io.BytesIO(imgTemp.getvalue())).getPage(0)
	overlayWHITE = PdfFileReader(io.BytesIO(imgTempWHITE.getvalue())).getPage(0)
	page.mergePage(overlay)
	page.mergePage(overlayWHITE)
	page.mergePage(new_pdf.getPage(0))

def download_from_url(contest_id, problem_index):
	file_name = contest_id + '-' + problem_index + '.pdf'
	problem_url = 'https://codeforces.com/problemset/problem/' + contest_id + '/' + problem_index
	pdfkit.from_url(problem_url, file_name)
	return file_name
	
	
def crop_pdf(file_name, letter, title):
	with open(file_name, "rb") as input_pdf:
		input_pdf = PdfFileReader(input_pdf)
		output_pdf = PdfFileWriter()
		default_box_page = {0:{'trimLowerLeft':(0,0),'trimUpperRight':(400,685), 'cropLowerLeft':(0,0), 'cropUpperRight':(400,685)}, 
							1:{'trimLowerLeft':(0,0),'trimUpperRight':(400,842), 'cropLowerLeft':(0,0), 'cropUpperRight':(400,842)}} 
		
		
		numPages = input_pdf.getNumPages()
		for i in range(numPages):
			page = input_pdf.getPage(i)
			print("pagina",i+1,":","Ancho x Alto  =", page.mediaBox.getUpperRight_x(),"x", page.mediaBox.getUpperRight_y())
			page.trimBox.lowerLeft = default_box_page[int(i > 0)]['trimLowerLeft']
			page.trimBox.upperRight = default_box_page[int(i > 0)]['trimUpperRight']
			page.cropBox.lowerLeft = default_box_page[int(i > 0)]['cropLowerLeft']
			page.cropBox.upperRight = default_box_page[int(i > 0)]['cropUpperRight']
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
			contest_id,problem_index,letter,title = line.split()
			file_name = download_from_url(contest_id,problem_index)
			crop_pdf(file_name,letter,title.replace('_',' '))
			letters.append(letter)
	
	
	final_output = PdfFileMerger()
	for letter in sorted(letters):
		merger.append(PdfFileReader(file(letter + '.pdf', 'rb')))
	final_output.write(contest + '.pdf')
		
			
if __name__ == '__main__':
	main()
 
