import requests
import pandas as pd
import sys
import geocoder
import numpy as np
import geopy.distance
from pprint import pprint
#from geopy import distance
from dicts import *
import os

#Czyszczenie terminala
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class Unziper:

    def __init__(self, maxpage = 10):
        self.maxpage = maxpage
        
    def get_current_loc(self):
        #pobiera obecna lokalizacje - na podstawie wyszukiarki, jezeli nie znajdzie, to na podstawie adresu IP (mniej dokladne)
        try:
            print("===============")
            print("Pobieram obecną lokalizację...")
            q = input("Podaj swój adres: ")
            rq = f'https://nominatim.openstreetmap.org/search.php?q={q}&format=jsonv2'
            get = requests.get(rq).json()
            lat, long = float(get[0]['lat']), float(get[0]['lon'])
            self.loc = [lat, long]
            print("")
            print(f"Znaleziona lokalizacja: ", ', '.join(get[0]['display_name'].split(", ")[-4:]))
        except:
            try:
                print("Szukam po lokalizacji IP...")
                self.loc = geocoder.ip('me').latlng
                print("Znalezione współrzędne: ", self.loc)
            except:
                print("Błąd w określaniu lokalizacji", sys.exc_info())
                self.loc = (0,0)
        finally:
                return self.loc
 
    def get_voiv(self):
        #na podstawie slownika zmienia nazwe wojewodztwa na jego kod - niezbedne do API MZ
        try:
            prov = input("Podaj nazwę województwa: ")
            for index, name in PROVINCE_DICT.items():
                if name == prov:
                    self.province = index
        except:
            print("Błędne województwo.")
            exit()
           
    def find_by_date(self):
        #szuka najblizszego terminu w najblizszym czasie
        try:
            i = 0
            while True:
                x = self.df.iloc[i].rename(VIEW_DICT)
                cls()
                print('==============================================')
                print(f"Najbliższy termin wypada {x['date']} (stan na: {x['date-situation-as-at']})")
                print('==============================================')
                print("DANE SZCZEGÓŁOWE:")
                #with pd.option_context('display.max_colwidth', 100):  # more options can be specified also
                pprint(x[list(VIEW_DICT.values())])
                print("")
                nx = input("Naciśnij enter, zeby przejsc dalej. 0 - wyjście do menu: ")
                if nx == '0':
                    break
                    cls()
                else: i +=1
        except:
            print("===============")
            print("Nie ma więcej dostępnych lokalizacji")
            print("Wracam do menu...")
            print("===============")
    
    def find_by_loc(self):
        #szuka najnowszego rekordu w odleglosci do podanego limitu
        try:
            max_dist = input("Podaj maksymalną odległość od swojej lokalizacji: ")
            i = 0
            while True:
                x = self.df[self.df['distance'] < int(max_dist)].iloc[i].rename(VIEW_DICT)
                cls()
                print('==============================================')
                print(f"DYSTANS: {round(x['ODLEGŁOŚĆ (KM)'],2)} km")
                print(f"MAKSYMALNY DYSTANS: {max_dist} km")
                print(f"Najbliższy termin wypada {x['date']} (stan na: {x['date-situation-as-at']})")
                print('==============================================')
                print("DANE SZCZEGÓŁOWE:")
                #with pd.option_context('display.max_colwidth', 100):  # more options can be specified also
                pprint(x[list(VIEW_DICT.values())])
                print("")
                nx = input("Naciśnij enter, zeby przejsc dalej. 0 - wyjście do menu: ")
                if nx == '0':
                    break
                    cls()
                else: i +=1
        except IndexError:
            print("===============")
            print("Nie ma więcej lokalizacji w tak małej odległości")
            print("Wracam do menu...")
            print("===============")
    
   
    def calc_dist(self):
        #liczy geodezyjna odleglosc miedzy dwoma punktami (lat, long)
        print("===============")
        self.df['distance'] = self.df.apply(lambda row: geopy.distance.geodesic((row.latitude, row.longitude) if ~np.isnan(row.latitude) else (0,0),tuple(self.loc)).km if ~np.isnan(row.latitude) else np.nan, axis = 1)
        
    def add_pages_pandas(self):
        #pobiera dane z <maxmage> stron, rozpakowuje jsona i wklada dane do dataframe'a
        data = []
        attr = []
        print("===============")
        print("Dodaję rekordy...")
        try:
            for page in range(1,self.maxpage+1):
                dt = requests.get(f'https://api.nfz.gov.pl/app-itl-api/queues?page={page}&limit=25&case=1&province={self.province}&benefit={self.bnf}&api-version=1.3').json()['data']
                data.append(dt)
                self.data = data
            for j in range(0,len(self.data)):
                for i in self.data[j]:
                    attr.append(i['attributes'])
            self.df = pd.concat([pd.DataFrame(attr).drop(['dates'], axis=1), pd.DataFrame(attr)['dates'].apply(pd.Series)], axis=1)
            print("Rekordy dodane.")
        except:
            print("Błąd przy dodawaniu rekordów: ", sys.exc_info())

    def get_benefit(self):
        # pobiera szukany benefit z inputu
        try:
            self.bnf = input("Podaj nazwę usługi do wyszukiwania: ")
        except:
            print("Błąd przy wprowadzaniu benefitu", sys.exc_info())


    def run(self):
        #uruchomienie aplikacji + menu
        cls()
        print("WYSZUKIWARKA TERMINÓW USŁUG MEDYCZNYCH")
        print("===============")
        self.get_voiv()
        self.get_benefit()
        self.add_pages_pandas()
        self.get_current_loc()
        self.calc_dist()
        #menu glowne
        while True:
            sett = input("\n Wybierz opcję: \n 1 - Wyświetl pierwszy wolny termin w województwie, \n 2 - Wyświetl pierwszy wolny termin w lokalizacji do X km, \n 0 - Wyjście\n Wybrana opcja: ")
            if sett == '1':
                self.find_by_date()
            elif sett == '2':
                print("================")
                self.find_by_loc()
            elif sett == '0':
                print("Wyjście z aplikacji.")
                break
            else:
                print("Błąd przy wyborze opcji")


uz = Unziper()
uz.run()