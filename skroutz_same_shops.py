import numpy as np
import requests
import csv
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from necessary_functions.check_times import check_if_and_times
from necessary_functions.class_shop import Shops


#----Read a .txt file that contains the product urls 
url = []
n_products = 0
with open('product_urls.txt', 'r+', newline='') as products:
    for product in products:
        url.append(product.strip())
        n_products = n_products + 1

print('Number of products:', n_products)
#------------------------------------------------------

#------Find the shops that provide all products--------
tot_counter = np.zeros(n_products, dtype=int)
urls = []
parts = [None]*4
headers={'Host': 'www.skroutz.gr' ,'User-Agent': 'Mozilla/5.0'}

for i in range(n_products):    
    html = requests.get(url[i], headers = headers)
    soup = BeautifulSoup(html.content, 'lxml')
    results = soup('li', class_ = ['card js-product-card', 'card js-product-card has-pro-badge'])
    shop_count = 0
    
    #find the common shops by comparing shop ids
    for result in results:
        shop_ids = result.get('id', None)
        parts = shop_ids.split('-')
        shop_id = int(parts[1])
        urls.append(shop_id)
        shop_count = shop_count + 1

    #Keep the total number of shops that provide each product
    tot_counter[i] = shop_count

#The ids of common shops are kept in sim_indices[]
sim_indices = []
sim_tot = np.zeros(n_products-1, dtype=int) #tracks the number of shops per 2,3,4... products
for i in range(2, n_products+1):
    pos_count = 0
    for j in range(len(urls)):
        #count only the unique indices
        if urls.count(urls[j]) == i and sim_indices.count(urls[j]) < 1:
            sim_indices.append(urls[j])
            pos_count = pos_count + 1
    
    sim_tot[i-2] = pos_count
    print(i, 'of the products can be found in', pos_count, 'shops')

#We are looking for the shop that has the most products that can be found at the bottom of the list
last_nonzero = np.max(np.nonzero(sim_tot))
optimal_list = sim_indices[-sim_tot[last_nonzero]:]
#----------------------------------------------------------

#--------Web scrap each link to retrieve the rest shop attributes-----
if len(sim_indices) >= 1:
    shop_strings = []
    for j in range(len(optimal_list)):
        shop_strings.append('shop-'+str(optimal_list[j]))

    #write csv file    
    f = open('Skroutz_shops.csv', 'w', encoding='UTF8', newline='')
    header = ['Product', 'Shop name', 'Shop url', 'Initial price', 'Skroutz transportation fees', 'Skroutz transaction fees', 'Shop transportation fees',
             'Shop transaction fees', 'Rating', 'Total reviews', 'Availability', 'Location']
    wr = csv.writer(f)
    wr.writerow(header)

    for i in range(n_products):
        try: #in case the product is available in the shop            
            p = Shops(url[i], shop_strings)    
            product = p._product_name()
            shop_url = p._shop_url()
            name = p._name()
            price = p._prices()
            rating, tot_rev = p._rating()
            avail = p._availability()
            loc = p._location()
            #----------------------------------------------------------------

            #------------------Print the results in the csv file--------------------
            for j in range(len(name)):
                if j == 0:
                    wr.writerow([product, name[j], shop_url[j], price[j,0], price[j,1], price[j,2], price[j,3],
                    price[j,4], rating[j], tot_rev[j], avail[j], loc[j]])
                else:
                    wr.writerow(['>>', name[j], shop_url[j], price[j,0], price[j,1], price[j,2], price[j,3],
                    price[j,4], rating[j], tot_rev[j], avail[j], loc[j]])

            wr.writerows('-')        
            #---------------------------------------------------------------------- 
        except:
            print('Product not available in shop number', i+1)       
else:
    print('No common shops were found in the provided urls.')
#---------------------------------------------------------------------

