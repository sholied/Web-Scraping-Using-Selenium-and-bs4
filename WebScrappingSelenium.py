#define the libraries we need
from operator import index
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import pandas as pd
import os
from bs4 import BeautifulSoup as soup

#we need to bypass the caphta using options
options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("--headless")
options.add_argument("--disable-extensions")
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

#define the fuction to get all links of e-bikes for single page
def get_all_links_single_page(driver, n_time):
    all_links = []
    wait = WebDriverWait(driver, n_time)
    elems = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
    for elem in elems:
        href = elem.get_attribute('href')
        if href is not None:
            #print(href)
            all_links.append(href)
    links_bikes = list(filter(lambda x: 'https://www.bike24.com/p' in x and len(x)==36, all_links))
    return links_bikes

#define save file to txt
def save_links_to_file(links):
    textfile = open("links.txt", "w")
    for element in links:
        textfile.write(element + "\n")
    textfile.close()


#define function to get all links for all pages fo e-bikes
def get_all_links_all_pages(driver, n_time):
    wait = WebDriverWait(driver, n_time)
    links_all_pages = get_all_links_single_page(driver, 20)
    print("Navigating to Page 1")
    time.sleep(1)

    all_links = []
    counter = 0
    while True:
        counter+=1
        try:
            next_btn = "/html/body/main/div/div[2]/div[3]/div[1]/div[3]/div/div/div[1]/a[2]"
            nb = wait.until(EC.element_to_be_clickable((By.XPATH, next_btn))).click()
            time.sleep(1)
            links_all_pages.extend(get_all_links_single_page(driver, 20))
            all_links.extend(links_all_pages)
            print("Navigating to Page {}".format(counter+1))
        except (TimeoutException, WebDriverException) as e:
            print("Last page reached")
            break
    all_links_pages = list(dict.fromkeys(all_links))
    return all_links_pages

    
#define function to scrapy data
def scraping_data(my_url, n_time):
    driver = webdriver.Chrome(options=options, service=s)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'})
    driver.get(my_url)
    time.sleep(3)
    wait = WebDriverWait(driver, n_time)
    wait.until(EC.element_to_be_clickable((By.XPATH, button_cookies))).click()
    time.sleep(3)
    fact_btn = "//*[@id='productDetail']/div[2]/div[1]/div[3]/label"
    x = wait.until(EC.presence_of_element_located((By.XPATH, fact_btn)))
    driver.execute_script("arguments[0].click();", x)

    html = driver.execute_script('return document.documentElement.outerHTML')
    so = soup(html, 'html.parser')
    datas = []
    table = so.find('table', {"class":"product-detail-data-sheet__table"})
    table_body = table.find('tbody')
    rows = table.find_all('tr')
    for row in rows[:3]:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        datas.append([ele for ele in cols if ele])

    data = [datas[0][1], datas[1][1], datas[2][1]]
    time.sleep(3)
    driver.quit() 
    return data

#run script to get all links
s=Service('C:\Program Files (x86)\chromedriver.exe')
#browser = webdriver.Chrome(ChromeDriverManager().install(), options=options) #if we dont have chromedriver.exe file
browser = webdriver.Chrome(options=options , service=s)
browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
browser.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'})
url = "https://www.bike24.com/e-bikes.html"
browser.get(url)
time.sleep(1)
button_cookies = '//*[@id="modal-root"]/div/div[2]/div[2]/div/div[1]/button[2]'
WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, button_cookies))).click()
if not os.path.exists("links.txt"):
    print("get links ....")
    links_all_pages = get_all_links_all_pages(browser, 20)
    save_links_to_file(links_all_pages)
    print("Total Links Collected that indicate of many data will collected is........{}".format(len(links_all_pages)))
else:
    print("Links already saved")
browser.quit()

#run script to scrapy all data
print("Start Scraping data------------")
with open("links.txt") as f:
    links_scarpy = f.read().splitlines()

f = open("e-bike2.csv", "w")
columns = "Product Name,Manufacturer,Item Code\n"
f.write(columns)
process = 0
for i in links_scarpy:
    time.sleep(1)
    print("\n")
    print('scraping data in links... "{}"'.format(i))
    x = scraping_data(i, 20)
    f.write(x[0] + "," + x[1] + "," + x[2] + "\n")
    process += 1
    if process % 5 == 0:
        print("We have {} datas total saved".format(process))
        print("\n------------------------sleep for 10 seconds to bypass Captha detection-------------------\n")
        time.sleep(10)
        if process % 20 == 0:
            print("\n-----------Sleep 20 seconds again after reach 20 datas for avoiding error timeout detection---------\n")
            time.sleep(20)
        else:
            continue
    else:
        continue

f.close()

print("\nfinish-----------")