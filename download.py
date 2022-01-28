import bs4
import requests
import os

url = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/return_periods/precipitation/KOSTRA/KOSTRA_DWD_2010R/asc/"
dir = "raw"


def get_raw(dir="raw"):
    """download kostra raw data from opendata.dwd.de"""
    try:
        os.makedirs(dir)
    except:
        pass
    r = requests.get(url)
    data = bs4.BeautifulSoup(r.text, "html.parser")
    for l in data.find_all("a"):
        file = l["href"]
        r = requests.get(os.path.join(url, file))
        try:
            open(os.path.join(dir, l["href"]), "wb").write(r.content)
            print("download: ", os.path.join(url, file))
        except:
            print("passing: ", os.path.join(url, file))


if __name__ == "__main__":
    get_raw()

# read_url("https://opendata.dwd.de/climate_environment/CDC/grids_germany/return_periods/precipitation/KOSTRA/KOSTRA_DWD_2010R/asc/")
