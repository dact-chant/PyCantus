"""
This script collectes feasts list (name, feast code) from Cantus Database.
Creates CSV CD_feast_data.csv with this list.
"""

import requests
from bs4 import BeautifulSoup
import csv


base_url = "https://cantusdatabase.org/feasts"


feasts = []
for page in range(1, 18):
    url = f"{base_url}?page={page}"
    print(f"Scraping: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", class_="table table-bordered table-sm small")
    if not table:
        print(f"Could not find data table on page {page}")
        continue

    tbody = table.find('tbody')
    for tr in tbody.findAll('tr'):
        cells = tr.find_all('td', class_='text-wrap')
        a = cells[0].find('a')
        feast_name = a.text

        feast_code = cells[3].text 
        feasts.append((feast_name.strip(), feast_code.strip()))



with open('CD_feast_data.csv', 'w', newline='') as fh:
    writer = csv.writer(fh)
    writer.writerow(['feast', 'feast_code'])
    writer.writerows(feasts)

print("\nSaved feast data to CD_feast_data.csv")