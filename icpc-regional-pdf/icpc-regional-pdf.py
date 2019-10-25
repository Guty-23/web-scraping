###################################################################################
#                                                                      	          #
#						getPDF version 2.0  				          	          #
#																		          #
###################################################################################
#                                                        				          #
#		The script starts with a menu and offers you two choices, download all 	  #
#	live-archive problems, or download only a specific regional. To make a		  #
#	choice you need to type the number that corresponds with your choice and	  #
# 	press "Enter"/"Return". 													  #
#	 	If you choose the second option, you will be shown another menu that	  #
#	allows you to choose the specific year of the regional you want to download,  #
#	and after that, a third menu asking you the specific regional contest.		  #	
#		After choosing a contest, a folder with the corresponding name is created # 
#	and all the problems will be downloaded there, along with a .pdf that 		  #
#	contains all the problems in a single file.               					  #
#	                                                                   	          #
###################################################################################
#                                                                      	          #
#	TO DO LIST:                                                   	          	  #
#		* On some cases there is no high-quality .pdf, but a lower quality one	  #
#		can be downloaded.														  #
#		* On other cases, where there is no .pdf at all, a text that documents 	  #
#		what happened should be added.											  #
#			                                	          #
#		                                                                          #
#																	 	          #
###################################################################################
#                                                                                 #
#	Things you may have to do:                                                    #
#                                                                                 #
#		1) Downlaod pip and type on the terminal:                                 #
#		"sudo pip install beautifulsoup4"                                         #
#		"sudo pip install requests"                                               #
#		"sudo pip install pyPDF2"                                                 #
#                                                                                 #
#		2) (Only maybe) On: "usr/local/lib/python2.7/dist-packages/PyPDF2"        #
#                                                                                 #
#	you should change the permissions on the file "generic.py" by doing:          #
#	"sudo chmod 777 /usr/local/lib/python2.7/dist-packages/PyPDF2/generic.py"     #
#                                                                                 #
#		3) (Only maybe) On "generic.py" you should modify lie 576 where it says:  #
#                                                                                 #
#		if not data.get(key):                                                     #
#			data[key] = value                                                     #
#		elif pdf.strict:                                                          #
#			# multiple definitions of key not permitted                           #
#			raise utils.PdfReadError("Multiple definitions in dictionary ...      #
#		else:                                                                     #
#			warnings.warn("Multiple definitions in dictionary ...                 #
#                                                                                 #
#		you should put this instead:                                              #
#                                                                                 #
#		if data.has_key(key):                                                     #
#			pass                                                                  #
#		else:                                                                     #
#			data[key] = value                                                     #
#                                                                                 #
#		4) After that, you can simply run the script.                             #
#		                                                                          #
###################################################################################                                                                   



import requests,os,bs4,sys
from PyPDF2 import PdfFileMerger

def get_page_from_url(url):
	page = requests.get(url) 
	soup = bs4.BeautifulSoup(page.text,'lxml') 
	links = soup.select('a') 
	return [page,soup,links]

def get_page_from_link(url,link):
	name = link.getText().replace('/'," - ")
	page,soup,links = get_page_from_url(url + link.attrs['href']) 
	return [page,soup,links,name]

def link_filt(links, s1 = 'Ap43JsNOhayCHANCEdeQUElePASESesteLINKa,RsZ1.,m', s2 = 'Ap43JsNOhayCHANCEdeQUElePASESesteLINKa,RsZ1.,m'):
	return [link for link in links if (link.attrs['href'][:5] == 'index' and not(link.getText() in ['Root','ICPC Archive Volumes',s1,s2])) ]

def download_from_url_to_path(url,name_of_folder,name_of_file):
		res = requests.get(url) 
		soupPDF = bs4.BeautifulSoup(res.text,'lxml') 
		if (len(soupPDF.select('h1')) == 0 and res.headers["Content-Length"] != "0"):
			pdf = open(os.path.join(name_of_folder,name_of_file + ".pdf"),"wb") 
			for chunk in res.iter_content(100000): 
				pdf.write(chunk)
			pdf.close()

def download_regional_from_link_to_path(url,links_regional,name_of_folder,contests_year,regional):
	os.makedirs(name_of_folder)
	combined = PdfFileMerger()
	for link_regional in link_filt(links_regional,contests_year,regional):
		page_problem,soup_problem,links_problem,problem = get_page_from_link(url,link_regional) 
		print(problem)
		for link_problem in links_problem: 
			if ('.pdf' == link_problem.attrs['href'][-4:]): 
				download_from_url_to_path(url + link_problem.attrs['href'],name_of_folder,problem)
				inpu = open(os.path.join(name_of_folder,problem + ".pdf"),"rb") 
				combined.append(inpu) 
	outpu = open(os.path.join(name_of_folder,contests_year + " - " + regional + ".pdf"),"wb")
	combined.write(outpu) 
	print(" - - - - ")
	
def main():
	try:
		requests.packages.urllib3.disable_warnings() # Not sure if this is always needed.
	except:
		pass

	root_url = 'https://icpcarchive.ecs.baylor.edu/index.php?option=com_onlinejudge&Itemid=8'
	url = "https://icpcarchive.ecs.baylor.edu/" 

	page_root,soup_root,links_root = get_page_from_url(root_url)

	print("What do you wish to download?\n")
	print("1 -> All Live Archive")
	print("2 -> A specific Regional/World Final")

	option = int(sys.stdin.readline())

	if option == 1:
		os.makedirs('Live Archive') 
		print("Downloading Live Archive... (it can take hours)")
		for link_root in link_filt(links_root):   
			page_year,soup_year,links_year,contests_year = get_page_from_link(url,link_root)
			os.makedirs('Live Archive/' + contests_year) 
			print("--------------\n--------------")
			print(contests_year)  
			print("--------------\n--------------")
			for link_year in link_filt(links_year,contests_year): 
				page_regional,soup_regional,links_regional,regional = get_page_from_link(url,link_year)
				print(regional)
				print(" - - - - ")
				download_regional_from_link_to_path(url,links_regional,'Live Archive/' + contests_year + "/" + regional,contests_year,regional)

	else:
		print("\nWorld Finals or Regional?")
		print("1 -> World Final")
		print("2 -> Regional")
		optionWFoR = int(sys.stdin.readline())
		if optionWFoR == 1:
			WF_LINK = 19
			print("\nWhich one?")
			page_year,soup_year,links_year,contests_year = get_page_from_link(url,links_root[WF_LINK])
			WF_List = list(enumerate(link_filt(links_year,contests_year)))
			for i,link_year in WF_List:
				print(i+1,"->",link_year.getText().replace("/", " - "))
			print("(list fully loaded)")
			contest = int(sys.stdin.readline())
			page_regional,soup_regional,links_regional,regional = get_page_from_link(url,WF_List[contest-1][1])
			print("--------------\n--------------")
			print(contests_year)  
			print("--------------\n--------------")
			print(regional)
			print(" - - - - ")
			download_regional_from_link_to_path(url,links_regional,regional,contests_year,regional)
		else:
			print("\nWhich year?")
			year_list = list(enumerate(link_filt(links_root,"World Finals")))
			for i,link_root in year_list:
				print(i+1,"->",link_root.getText().replace("/", " - "))
			year = int(sys.stdin.readline())
			page_year,soup_year,links_year,contests_year = get_page_from_link(url,year_list[year-1][1])
			print("--------------")
			print(contests_year)
			print("--------------")
			print("\nWhich region?")
			region_list = list(enumerate(link_filt(links_year,contests_year)))
			for i, link_year in region_list:
				print(i+1,"->",link_year.getText().replace("/"," - "))
			contest = int(sys.stdin.readline())
			page_regional,soup_regional,links_regional,regional = get_page_from_link(url,region_list[contest-1][1])
			print("--------------\n--------------")
			print(contests_year)
			print("--------------\n--------------")
			print(regional)
			print(" - - - - ")
			download_regional_from_link_to_path(url,links_regional,contests_year + " - " + regional,contests_year,regional)
			
			
	print("\nDownload complete.")
		
if __name__ == "__main__":
    main()
