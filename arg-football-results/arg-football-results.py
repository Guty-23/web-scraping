# Usa python3
import requests,datetime
from bs4 import BeautifulSoup

from match import Match

################################
# Constants to adapt each time #
################################

years = [2018,2019]
teams_each_year = {2018:26,2019:24}
start_each_year = {2018:1342,2019:2006}
finish_each_year = {2018:-195,2019:-135}
rounds_each_year = {2018:25,2019:13}
wikipedia_fields = 6

year_each_month = {year:{'january':year+1,'enero':year+1, 'february':year+1,'febrero':year+1, 
						  'march':year+1,'marzo':year+1, 'april':year+1,'abril':year+1,	'may':year+1,'mayo':year+1,
						  'june':year+1,'junio':year+1, 'july':year,'julio':year, 'august':year,'agosto':year,
						  'september':year,'septiembre':year,'setiembre':year, 'october':year,'octubre':year, 
						   'november':year,'noviembre':year, 'december':year,'diciembre':year} for year in years}

index_each_month = {year:{'january':1,'enero':1, 'february':2,'febrero':2, 'march':3,'marzo':3, 'april':4,'abril':4,
					'may':5,'mayo':5,'june':6,'junio':6, 'july':7,'julio':7, 'august':8,'agosto':8,
					'september':9,'septiembre':9,'setiembre':9, 'october':10,'octubre':10, 
					'november':11,'noviembre':11, 'december':12,'diciembre':12} for year in years}
					
index_datetime_day = {0:'monday', 1:'tuesday', 2:'wednesday', 3:'thursday', 4:'friday', 5:'saturday', 6:'sunday'}

def get_matches_from_wikipedia(soup,teams,rounds,rows,year):

    matches_raw = [['' for x in range(wikipedia_fields)] for row in range(rows)]
    i = 0
    start = start_each_year[year]   # Search on the table watching HTML from wikipedia, aided by bs4
    finish = finish_each_year[year] # Search on the table watching HTML from wikipedia, aided by bs4
    
    for x in soup.select('table tbody tr td')[start:finish]:
        while(i < wikipedia_fields*rows and matches_raw[i//wikipedia_fields][i%wikipedia_fields] != ''):
            i += 1
        if i < wikipedia_fields*rows:
            field = x.getText().strip().split('[')[0]
            if field == '':
                field = "Entry without value"
            if i % wikipedia_fields == 4:  # Date
                day_month = list(map(lambda s : s.strip().lower(),field.split(' de ')))
                field = datetime.date(year_each_month[year][day_month[1]], index_each_month[year][day_month[1]], int(day_month[0]))
            k = 1
            if x.get('rowspan') != None:
                k = int(x.get('rowspan'))
            for j in range(k):
                matches_raw[i//wikipedia_fields+j][i%wikipedia_fields] = field
    
    match_list = []
    for match in matches_raw:
        hours, minutes = list(map(int, match[5].split(':')))
        home_goals,away_goals = match[1].split('-')
        home,away = match[0],match[2]
        stadium = match[3]
        date = datetime.datetime(match[4].year, match[4].month, match[4].day, hours, minutes)
        match_list.append(Match(date,stadium,home,away,home_goals,away_goals))
    
    return match_list
       
def main():

	for year in years:
		print("\n\n\n#######################\n# Superliga " + str(year) + "-" + str(year+1) + " #\n#######################\n")
		wiki = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_División_" + str(year) +"-" + str(year+1)[2:] + "_(Argentina)"
		website_url = requests.get(wiki).text
		soup = BeautifulSoup(website_url,'lxml')

		teams = teams_each_year[year]
		rounds = rounds_each_year[year]
		rows = (teams//2)*rounds
		
		match_list = sorted(get_matches_from_wikipedia(soup,teams,rounds,rows,year))
		for m in match_list:
			print(m)
			

if __name__ == '__main__':
	main()
    
        
    # TO DO: Hacer mejor con pandas.

    
    # nombres_equipos = equipos = sorted(list(set([p[0] for p in partidos])))
    # for eq in nombres_equipos:
    #     dia_horario_local = {}
    #     dia_horario_visitante = {}
    #     dia_horario_total = {}
    #     for p in partidos:
    #         tupla_horario = (p[4].weekday(), p[5])
    #         if p[0] == eq or p[2] == eq:
    #             if not tupla_horario in dia_horario_total.keys():
    #                 dia_horario_total[tupla_horario] = 0
    #                 dia_horario_local[tupla_horario] = 0
    #                 dia_horario_visitante[tupla_horario] = 0
    #             dia_horario_total[tupla_horario] += 1
    #             if p[0] == eq:
    #                 dia_horario_local[tupla_horario] += 1
    #             else:
    #                 dia_horario_visitante[tupla_horario] += 1
    #
    #     suma_partidos = 0
    #     # print("\n#############\n " + eq + "\n#############\n")
    #     # print("TOTAL,LOCAL,VISITANTE:\n")
    #     for c,h in sorted([(dia_horario_total[x],x) for x in dia_horario_total.keys()], reverse = True):
    #         suma_partidos += c
    #         # print(indice_datetime_a_dia[h[0]] + " " + h[1], "--> ", str(c) + ", " + str(dia_horario_local[h]) + ", " + str(dia_horario_visitante[h]))
    #     assert(suma_partidos == fechas)



