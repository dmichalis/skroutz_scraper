import numpy as np
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from necessary_functions.check_times import check_if_and_times

class Shops(object):
    #Retrieve data for each shop#

    def __init__(self, url, shops): 
        self.driver = webdriver.Chrome() 
        self.driver.get(url)
        html = requests.get(url)
        self.shops = shops    
    
    #----------Get the product name--------------
    def _product_name(self):
        product_name = self.driver.find_element(By.XPATH, f"//h1[@class='page-title']").text

        return product_name
    #---------------------------------------------------    

    #----------Get the shop url--------------
    def _shop_url(self):
        url_shop = []
        for shop in self.shops:
            try: #shop
                elem1 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{shop}']/div[1]/div[2]/div[@class='item']/h3/a")))
            except: #skroutz
                elem1 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{shop}']/div[1]/div[2]/div[@class='item with-ndd']/h3/a")))  
            url_shop.append(elem1.get_attribute('href'))

        return url_shop
    #---------------------------------------------------

    #-------Get the name of each shop-------------
    def _name(self):
        name = []
        for shop in self.shops:
            elem2 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{shop}']/div[1]/div[1]/div[1]/p")))
            name.append(elem2.text)
    
        return name
    #--------------------------------------------

    #----------Get the total price with transportation and exchange fees--------------
    def _prices(self):
        prices = np.zeros((len(self.shops), 5))

        for i in range(len(self.shops)):
            elem3 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{self.shops[i]}']/div[2]/div[@class='price-content']")))
            fees_string = elem3.text.replace(',','.')
            fees = fees_string.split()

            try:
                #Depending on whether the product is provided by skroutz or shop the length of the matrix changes
                store = 'κατάστημα'
                sk = 'Skroutz'
                times_store = check_if_and_times(store, fees)
                times_skroutz = check_if_and_times(sk, fees)
                #concanate terms to shorten if clause
                posib = str(times_store)+str(times_skroutz)
                
                #isolate the float number from the string
                iso_prices = [float(iso_prices) for iso_prices in re.findall(r'\d+\.?\d*', fees_string)]

                #fill the prices matrix for each product
                prices[i,0] = iso_prices[0]
                if posib == '01':
                    prices[i,1] = iso_prices[1]
                    prices[i,2] = iso_prices[2]
                elif posib == '10':
                    prices[i,3] = iso_prices[1]
                    prices[i,4] = iso_prices[2]
                elif times_store == 1 and times_skroutz == 1: 
                    prices[i,1] = iso_prices[1]
                    prices[i,2] = iso_prices[2]
                    prices[i,3] = iso_prices[4]
                    prices[i,4] = iso_prices[5]
            except:
                #Could not retrieve additional fees
                prices[i,0] = iso_prices[0]
                for j in range(1,5):
                    prices[i,j] = 0

        return prices
    #---------------------------------------------
    
    #-------Get the rating of each shop-------------
    def _rating(self):
        rating = []
        total_reviews = []
        for i in range(len(self.shops)):
            elem4 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{self.shops[i]}']/div[1]/div[@class='shop']/div/div[2]/a/div")))
            rating.append(float(elem4.text.split()[1]))     
            total_reviews.append(int(elem4.text.split()[0]))
    
        return rating, total_reviews
    #--------------------------------------------

    #-------Get the availability in each shop-------------
    def _availability(self):
        availability = []
        for shop in self.shops:
            try: #shop
                elem5 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{shop}']/div[1]/div[@class='description']/div/div/p/span")))
                availability.append(elem5.text)
            except: #skroutz
                elem5 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{shop}']/div[1]/div[@class='description']/div/div/div[@class='ndd-wrapper']/p/span")))
                text = elem5.text.split()
                availability.append(text[0] + ' ' + text[1] + ' ' + text[2])    
            
        return availability
    #--------------------------------------------

    #-------Get the location of each shop-------------
    def _location(self):
        location = []
        for shop in self.shops:
            elem6 = WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, f"//li[@id='{shop}']/div[1]/div[2]/div/div[@class='product-info']/span")))
            if len(elem6.text.split()) == 2:
                location.append(elem6.text.split()[0].split(',')[0] + ':' + elem6.text.split()[1])
            else:    
                location.append(elem6.text.split()[0])

        return location
    #--------------------------------------------
    
    def __del__(self):
        self.driver.close() 
