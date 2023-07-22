import os
import requests
import random
from bs4 import BeautifulSoup
import pandas as pd

total_records = 0
reqLimit = 5
start_url = 'https://catcar.info'
final_output = "final_results_car_info2.csv"

get_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

def getProxy():
    ips_path = "ips-faizan.txt"
    with open(ips_path, "r") as ipsFile:
        proxList = [ip.strip() for ip in ipsFile.readlines()]
        
    i = 0
    while i < len(proxList):
        try:
            print(f"_Attempt#_{i}", end="\r", flush=True)
            proxy_info = random.choice(proxList).split(":")
            proxy_host = proxy_info[0]
            proxy_port = proxy_info[1]
            proxy_username = proxy_info[2]
            proxy_password = proxy_info[3]
            proxy = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
            
            resp = requests.request(
                "GET",
                "https://www.google.com/",
                proxies={"http": proxy, "https": proxy},
                timeout=5,
            )
            
            if resp.status_code == 200:
                print("PROXY FOUND")
                return proxy
        except:
            i += 1
            continue

    raise Exception("All proxies are not working!")

proxy = getProxy()

def getResponse(url):
    reqCount = 0
    while reqCount < reqLimit:
        try:
            resp = requests.request(
                "GET", url, headers=get_headers, proxies={"http": proxy, "https": proxy}, timeout=10
            )
            if resp.status_code == 200:
                return resp
        except:
            proxy = getProxy()
            reqCount += 1

    raise Exception(f"Failed to get a valid response from {url}")

# ----------------------------Market/model-----------------------#
# ---------------------------------------------------------------#
url = 'http://catcar.info/audivw/?lang=en&l=c3RzPT17IjEwIjoiQnJhbmQiLCIyMCI6IlZXIn18fHN0PT0yMHx8YnJhbmQ9PXZ3'
try:
    resp = getResponse(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    main_rows = soup.find_all('tr')[1:]
    print(resp)
    for main_row in main_rows:
        try:
            macells = main_row.find_all('td')
            model_cell = macells[1]
            model = model_cell.text.strip()
            model_link = model_cell.a['href']

            model_year_resp = getResponse(model_link)
            model_year_soup = BeautifulSoup(model_year_resp.content, 'html.parser')
            table = model_year_soup.find('table', class_='table')
            year_rows = table.find_all('tr')[1:]

            for year_row in year_rows:
                year_cells = year_row.find_all('td')
                car_model = year_cells[0].text.strip()
                year_link = year_cells[1].find('a')
                year = year_link.text.strip()
                main_parts_link = year_link['href']

                main_parts_resp = getResponse(main_parts_link)
                main_parts_soup = BeautifulSoup(main_parts_resp.content, 'html.parser')
                items = main_parts_soup.find_all('a', class_='groups-parts__item')

                for item in items:
                    part_title = item.find('span', class_='groups-parts__title').text
                    sub_group_link = item['href']

                    sub_group_resp = getResponse(sub_group_link)
                    sub_group_soup = BeautifulSoup(sub_group_resp.content, 'html.parser')
                    sub_rows = sub_group_soup.find_all('tr')[1:]

                    for sub_row in sub_rows:
                        sub_cells = sub_row.find_all('td')
                        ill_no = sub_cells[1].find('a').text
                        sub_group_description = sub_cells[2].text.strip()
                        parts_link = sub_cells[1].find('a')['href']

                        parts_page_resp = getResponse(parts_link)
                        parts_soup = BeautifulSoup(parts_page_resp.content, 'html.parser')
                        parts_rows = parts_soup.find_all('tr')[1:]

                        # Getting image
                        img_wrapper_div = parts_soup.find('div', class_='img_wrapper')
                        img_link = None
                        if img_wrapper_div:
                            img_tag = img_wrapper_div.find('img')
                            if img_tag and 'src' in img_tag.attrs:
                                img_link = img_tag['src']

                        for parts_row in parts_rows:
                            basket_td = parts_row.find('td', class_='table__td table__td--basket')
                            if basket_td and basket_td.find('a'):
                                part_cells = parts_row.find_all('td')
                                part_number_element = part_cells[2].find('a')
                                part_number = part_number_element.text.strip() if part_number_element else None
                                description = part_cells[3].text.strip() if len(part_cells) > 3 else None
                                remark = part_cells[4].text.strip() if len(part_cells) > 4 else None
                                st = part_cells[5].text.strip() if len(part_cells) > 5 else None
                                model_data = part_cells[6].text.strip() if len(part_cells) > 6 else None

                                total_records += 1
                                data_list = [{
                                    'page_url_id': total_records,
                                    'page_link': parts_link,
                                    'img_link': img_link,
                                    'main_model': model,
                                    'car_model': car_model,
                                    'model_year': year,
                                    'part_title': part_title,
                                    'ill_no': ill_no,
                                    'sub_group_description': sub_group_description,
                                    'part_description': description,
                                    'part_Remark': remark,
                                    'part_st': st,
                                    'part_model_data': model_data
                                }]

                                print(f"Records processed: {total_records}", end="\r", flush=True)
                                df = pd.DataFrame(data_list)
                                df.to_csv(final_output, mode='a', index=False, header=not os.path.isfile(final_output))
        except Exception as e:
            print(f"Error: {e}")
            continue

except Exception as e:
    print(f"Error: {e}")
