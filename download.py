from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup

def read_url(url):
    url = url.replace(" ","%20")
    req = Request(url)
    a = urlopen(req).read()
    soup = BeautifulSoup(a, 'html.parser')
    x = (soup.find_all('a'))
    for i in x:
        file_name = i.extract().get_text()
        url_new = url + file_name
        url_new = url_new.replace(" ","%20")
        if(file_name[-1]=='/' and file_name[0]!='.'):
            read_url(url_new)
        print(url_new)

import bs4
import requests
import os

#url = "http://bossa.pl/pub/metastock/ofe/sesjaofe/"
url = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/return_periods/precipitation/KOSTRA/KOSTRA_DWD_2010R/asc/"
dir = "raw"
os.makedirs(dir)

r = requests.get(url)
data = bs4.BeautifulSoup(r.text, "html.parser")
for l in data.find_all("a"):
    file = l["href"]
    r = requests.get(os.path.join(url, file))
    print(r.status_code)
    try:
        open(os.path.join(dir,l["href"]), 'wb').write(r.content)
        print('download: ', os.path.join(url, file))
    except:
        print('passing: ', os.path.join(url, file))



#read_url("https://opendata.dwd.de/climate_environment/CDC/grids_germany/return_periods/precipitation/KOSTRA/KOSTRA_DWD_2010R/asc/")
