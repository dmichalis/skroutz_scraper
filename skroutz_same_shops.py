import numpy as np
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from check_times import check_if_and_times
from class_shop import Shops


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

for i in range(n_products):    
    driver = webdriver.Chrome() 
    driver.get(url[i])
    results = driver.find_elements(By.XPATH, "//*[@class='card js-product-card' or @class='card js-product-card has-pro-badge']")
    
    shop_count = 0
    #find the common shops by comparing shop ids
    for result in results:
        shop_ids = result.get_attribute('id')
        parts = shop_ids.split('-')
        shop_id = int(parts[1])
        urls.append(shop_id)
        shop_count = shop_count + 1

    driver.close()     
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
    if len(sim_indices) >= 1:
        print(i, 'of the products can be found in', pos_count, 'shops')


#--------Web scrap each link to retrieve the rest shop attributes-----
if len(sim_indices) >= 1:
    #We are looking for the shop that has the most products that can be found at the bottom of the list
    last_nonzero = np.max(np.nonzero(sim_tot))
    optimal_list = sim_indices[-sim_tot[last_nonzero]:]
    #----------------------------------------------------------

    shop_strings = []
    for j in range(len(optimal_list)):
        shop_strings.append('shop-'+str(optimal_list[j]))

    #Retrieve all characteristics of those shops that provide the majority of products
    for i in range(n_products):   
        p = Shops(url[i], shop_strings)    
        product = p._product_name()
        price = p._prices()
        count = np.count_nonzero(price == -1) #count how many negative values returned
        if count == len(shop_strings)*5:
            continue #if all values are negative skip this product
            
        #The following characteristics are common among all products so retrieve them only once
        if i == 0:
            shop_url = p._shop_url()
            name = p._name()
            rating, tot_rev = p._rating()
            avail = p._availability()
            loc = p._location()
    
            #initialize dataset
            info = {'Shop name': name, 'Shop url': shop_url, 'Skroutz transportation fees': price[:,1],
                    'Skroutz transaction fees': price[:,2], 'Shop transportation fees': price[:,3],
                    'Shop transaction fees': price[:,4], 'Rating': rating, 'Total Reviews': tot_rev, 
                    'Availability': avail, 'Location': loc}
            df = pd.DataFrame(info)
        
        #Add the initial price
        df.insert(2, product, price[:,0], True)
        #----------------------------------------------------------------------        
        
    df.to_csv('Skroutz_shops.csv')       
else:
    print('No common shops were found in the provided urls.')
#---------------------------------------------------------------------

