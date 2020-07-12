import requests,os
url_cases = 'http://maratona.ime.usp.br/hist/2019/resultados13/data/contest/A/input'
from bs4 import BeautifulSoup

for case in range(1,111+1):
	url = requests.get(url_cases + str(case)).text
	soup = BeautifulSoup(url,'lxml')
	for x in soup:
		for file_string in x.select('body p')[0]:
			with open("A_" + str(case) + ".in","wb") as input_case: 
				input_case.write(file_string)
	
	

