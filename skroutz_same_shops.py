import numpy as np
import pandas as pd
import requests
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from check_times import check_if_and_times
from class_shop import Shops
from collections import Counter 

#----------Read a .txt file that contains the product list_ids----------- 
url = []
n_products = 0
with open('product_urls.txt', 'r+', newline='') as products:
    for product in products:
        url.append(product.strip())
        n_products += 1

print('Number of products:', n_products)
#------------------------------------------------------------------------

#-------------------Find the all/unique shops-----------------------------
list_ids, name, nspp = [], [], [] #Number of Shops Per Product
for i in range(n_products):    
    driver = webdriver.Chrome() 
    driver.get(url[i])
    results = driver.find_elements(By.XPATH, "//li[@class='card js-product-card']")
    
    #Retrieve shop ids from Skroutz
    count = 0
    for result in results:
        shop_id = int(result.get_attribute('id').split('-')[1])
        list_ids.append(shop_id)
        count += 1

    nspp.append(count)    
    driver.close()     
#Count how many of the selected items each shop contains
unique_ids, count_unique, shop_strings = [], [], []    
for item in list_ids:    
    if item not in unique_ids: 
        unique_ids.append(item)

nus = len(unique_ids) #Number of Unique Shops
for item in unique_ids:
    count_unique.append(list_ids.count(item))   
#----------------------------------------------------------------------------------

#----------Web scrap each link to retrieve the corrsponding shop attributes---------
vols = 0 # Values Of List Selected
#Create arrays with length equal to the number of unique shops
#When the optimal cost is found the elements printed will come from these arrays
all_products, all_names, = [], []
all_prices = np.ones(( n_products ,nus))*10e+04 
all_fees = np.ones(( n_products, nus ))*10e+04
all_prov = [None]*nus
all_names = [None]*nus
all_shopurls = [None]*nus
all_ratings = np.zeros(nus)
all_rev = np.zeros(nus)
all_avail = [None]*nus
all_loc = [None]*nus

for i in range(n_products):
    #create an object for each product
    p = Shops(url[i], list_ids[vols:nspp[i]+vols]) #isolate the shop ids that provide each product    
    #----Get the product name and price
    product = p._product_name()
    all_products.append(product)
    #----Get the characteristics of each shop
    price = p._prices()
    shop_url = p._shop_url()
    name = p._name()
    rating, tot_rev = p._rating()
    avail = p._availability()
    loc = p._location()

    for j in range(len(shop_url)):
        if name[j] not in all_names:
            all_names.append(name[j])   
    #--------Fill the cells of the remaning arrays
    count = 0
    for item in list_ids[vols:nspp[i]+vols]:
        all_prices[i, unique_ids.index(item)] = price[count, 0]
        #Select Skroutz/shop delivery and favour Skroutz due to better delivery despite slightly higher fees
        if (price[count, 2] - price[count, 1]) <= 1:
            all_fees[i, unique_ids.index(item)] = price[count, 2]
            all_prov[unique_ids.index(item)] = 'Skroutz'
        else:
            all_fees[i, unique_ids.index(item)] = price[count, 1]
            all_prov[unique_ids.index(item)] = 'Store'
        
        all_shopurls[unique_ids.index(item)] = shop_url[count]
        all_ratings[unique_ids.index(item)] = rating[count]
        all_rev[unique_ids.index(item)] = tot_rev[count]  
        all_avail[unique_ids.index(item)] = avail[count]
        all_loc[unique_ids.index(item)] = loc[count]
        count += 1
    #------------------------------------------------
    vols += nspp[i] #increase by the number of shops corresponding to the next product
#---------------------------------------------------------------------------------------       

#---------------------------------------------------------------------------------------
#-------------------------Find that combination of shops with the smallest price-------------------------------
#Check which shops provide the most products and select the cheapest
ims = [] #Indice of Max Shops
for index in range(len(count_unique)):
    if count_unique[index] == max(count_unique):
        ims.append(index)
iopt = -np.ones(n_products, dtype=int) #Create an array that will contain the optimal indices
cost = 0
for j in range(len(ims)):
    for i in range(n_products):
        if all_prices[i,ims[j]] != 1.e+05:
            cost += all_prices[i, ims[j]]

    cost += all_fees[0,ims[j]] #add the fees from some row
    if j == 0: 
        min_cost = cost
        for i in range(n_products):
            if all_prices[i,ims[j]] != 1.e+05:
                iopt[i] = ims[j]

    if cost < min_cost:            
        min_cost = cost
        for i in range(n_products):
            if all_prices[i,ims[j]] != 1.e+05:
                iopt[i] = ims[j]
            else:
                iopt[i] = -1                                            
#------------------------------------------------------------------------------
#
#-----------From the remaining products select the cheapest shop--------------
iom = np.zeros(n_products, dtype=int) #Index Of Min in the remaining rows
conut = 0
for i in range(n_products):
    if all_prices[i, ims[i]] != 1.e+05:
        continue
    else:
        #find the indices of the shops with the minimum price -> find min price
        min1 = []
        for j in range(nus): 
            if all_prices[i,j] == np.amin(all_prices[i, :]):
                min1.append(j)
        min2 = all_prices[i, min1[0]] + all_fees[i, min1[0]]
        iom[i] = min1[0]
        for index in min1:
            if all_prices[i, index] + all_fees[i, index] < min2:
                min2 = all_prices[i, index] + all_fees[i, index]
                iom[i] = index
        #-------------------------
        #calculate the cost   
        min_cost += all_prices[i, iom[i]] + all_fees[i, iom[i]]
        iopt[i] = iom[i]
        if i > 0:
            if iom[i] == iom[i-1]:
                min_cost -= all_fees[i, iom[i]] #remove duplicate costs
#------------------------------------------------------------------------------
#
#----------------------------------------------------------------------------------------------------------

#initialize dataset
info = {'Product name': all_products[0], 'Starting price': all_prices[0, iopt[0]], 'Transportation fees': all_fees[0, iopt[0]], 
        'Buy via': all_prov[iopt[0]], 'Shop name': all_names[iopt[0]], 'Shop url': all_shopurls[iopt[0]], 'Rating': all_ratings[iopt[0]], 
        'Total Reviews': all_rev[iopt[0]], 'Availability': all_avail[iopt[0]], 'Location': all_loc[iopt[0]]}
df = pd.DataFrame(info, index=[0])

for i in range(1, n_products):
    df.loc[i] = [ all_products[i], all_prices[i, iopt[i]], all_fees[i, iopt[i]], all_prov[iopt[i]], all_names[iopt[i]], 
                all_shopurls[iopt[i]], all_ratings[iopt[i]], all_rev[iopt[i]], all_avail[iopt[i]], all_loc[iopt[i]] ]
df.to_csv('Skroutz_shops.csv', index=False)

