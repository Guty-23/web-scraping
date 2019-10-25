import requests,datetime
from bs4 import BeautifulSoup

equipos_por_anho = {2018:26,2019:24}
start_por_anho = {2018:1342,2019:2005}
finish_por_anho = {2018:-195,2019:-664}
fechas_por_anho = {2018:25,2019:13}
for anho in [2018,2019]:
    print("\n\n\n#######################\n# Superliga " + str(anho) + "-" + str(anho+1) + " #\n#######################\n")
    wiki = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_División_" + str(anho) +"-" + str(anho+1)[2:] + "_(Argentina)"
    website_url = requests.get(wiki).text
    soup = BeautifulSoup(website_url,'lxml')

    mes_al_anho = {'enero':anho+1, 'febrero':anho+1, 'marzo':anho+1, 'abril':anho+1,
                   'mayo':anho+1, 'junio':anho+1, 'julio':anho, 'agosto':anho,
                   'septiembre':anho, 'octubre':anho, 'noviembre':anho, 'diciembre':anho}

    mes_a_indice = {'enero':1, 'febrero':2, 'marzo':3, 'abril':4,
                   'mayo':5, 'junio':6, 'julio':7, 'agosto':8,
                   'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12}

    indice_datetime_a_dia = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}

    equipos = equipos_por_anho[anho]
    fechas = fechas_por_anho[anho]
    campos_wikipedia = 6
    rows = (equipos//2)*fechas

    partidos = [['' for x in range(campos_wikipedia)] for row in range(rows)]
    i = 0
    start = start_por_anho[anho]   # Buscar a ojo en unos minutos cuando empieza la tabla viendo el HTML de wikipedia, ayudado por bs4
    finish = finish_por_anho[anho] # Buscar a ojo en unos minutos cuando termina la tabla viendo el HTML de wikipedia, ayudado por bs4
    for x in soup.select('table tbody tr td')[start:finish]:
        while(i < campos_wikipedia*rows and partidos[i//campos_wikipedia][i%campos_wikipedia] != ''):
            i += 1

        campo = x.getText().strip().split('[')[0]
        if campo == '':
            campo = "Estadio no decidido"
        if i % campos_wikipedia == 4:  # Fecha
            dia_mes = list(map(lambda s : s.strip(),campo.split(' de ')))
            campo = datetime.date(mes_al_anho[dia_mes[1]], mes_a_indice[dia_mes[1]], int(dia_mes[0]))
        k = 1
        if x.get('rowspan') != None:
            k = int(x.get('rowspan'))
        for j in range(k):

            partidos[i//campos_wikipedia+j][i%campos_wikipedia] = campo

    # TO DO: Hacer mejor con pandas.

    for p in partidos:
        horas, minutos = list(map(int, p[5].split(':')))
        print(",".join(list(map(str, p[:4] + [datetime.datetime(p[4].year, p[4].month, p[4].day, horas, minutos)]))))
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



