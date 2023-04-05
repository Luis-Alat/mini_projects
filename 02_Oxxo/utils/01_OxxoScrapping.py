#!/usr/bin/env python
# coding: utf-8

# # Web Scrapping: oxxo stores

# This notebook is created to scrape the localization and some other information about Oxxo stores (which are very popular in Mexico) by using Google Maps.
# 
# Unfortunately, the official website of the store does not have the latest information and is not more user-friendly than Google Maps. For that reason, I chose maps as a better alternative.
# 
# On the other hand, the localization of the stores is only intended to be done for the Mexico City area (or CDMX in Spanish). However, in theory, the code (at least the web scraping section) should work for whatever search you wish.
# 
# Finally, there are comments throughout the notebook if you want to know more about the logic of the process. However, there is no intention for it to be a full tutorial. But, if it's useful for you, feel free to check it out.

# In[24]:


import time
import pandas as pd
import numpy as np
import re
import warnings
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


# In[25]:


class ScrapMaps:
    
    '''
    This class was created to do web scrapping on google maps searches
    
    Parameters
    ----------
    
        driver_path:str
            Path to find and load webdriver for Chrome browser
            
        sleep_time:int; default=2
            seconds to wait between each selenium execution on browser
            
    '''
    
    def __init__(self, driver_path:str, sleep_time:int=2):
        
        self.driver = webdriver.Chrome(service=Service(driver_path))
        self.sleep_time = sleep_time
    
    def DefineSearchStatus(self, class_name_results, class_name_partial):
        
        # This function checks if the search query returned a possible partial match, zero results
        # or multiples results
        
        # Status if the search query returns a partial match (False means no partial match)
        self.partial_match_status = False
        self.zero_results_status = False
                
        # Check if only one result was returned. It could be "partial match" status
        results = self.driver.find_elements(By.CLASS_NAME, class_name_results)
        if len(results) == 1:
            
            # Check if there is a partial message on web page
            check_partial_match = len(self.driver.find_elements(By.CLASS_NAME, class_name_partial))
            self.partial_match_status = True if check_partial_match else False
            
        if len(results) == 0:
            self.zero_results_status = True
    
    def SearchByUrl(self, url:str, xpath_search_buttom:str) -> bool:
        
        # This function use the url to place a search on google maps and click the search buttom
        
        self.url = url
        
        print(f"Seaching by url: {self.url}")
        self.driver.get(self.url)
        time.sleep(self.sleep_time)
        
        search_buttom = self.driver.find_element(By.XPATH, xpath_search_buttom)
        search_buttom.click()
        time.sleep(self.sleep_time + 1)
        
    def ScrollDownResults(self, xpath_element_results:str, class_name_results:str):
        
        '''
        This function scroll down in the results section found in the left of google maps
        
        Parameters
        ----------
        
            xpath_element_results: str
                xpath path to manipulate the results section and scroll down
            
            class_name_results: str
                class name to identify the number of results thrown by google maps found inside
                the xpath_element_results 
            
        '''
        
        print("Scrolling down...")
        n_before_scroll = len(self.driver.find_elements(By.CLASS_NAME, class_name_results))
        element_to_scroll = self.driver.find_element(By.XPATH, xpath_element_results)
        
        # Scroll down
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element_to_scroll)
        time.sleep(self.sleep_time)
        
        n_after_scroll = len(self.driver.find_elements(By.CLASS_NAME, class_name_results))
        
        # Scrolling until there are no new results
        while n_before_scroll != n_after_scroll:
            
            n_before_scroll = int(n_after_scroll)
            
            element_to_scroll = self.driver.find_element(By.XPATH, xpath_element_results)
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element_to_scroll)
            time.sleep(self.sleep_time)
            
            n_after_scroll = len(self.driver.find_elements(By.CLASS_NAME, class_name_results))
        
        print("No more results found")
        
    def GetResultsLocation(self, class_name:str, loc_attribute:str="href",
                           name_attribute:str="aria-label") -> dict:
        
        '''
        This function get latitude, longitude and name of the results got by google maps
        
        Parameters
        ----------
        
        class_name: str
            Common class name (HTML) of the results thrown by google maps
            
        loc_attribute: str
            Common attribute name (HTML) to find the url where is incrusted the
            latitude and longitude values. loc_attribute must be found in the class_name
            class
                
        name_attribute: str
            Common attribute name (HTML) to find the name of the result. name_attribute must
            be found in the class_name class
        
        Return
        ------
        
        dict: latitude, longitude and name of the results by google maps
        
        '''
        
        # Retrieving all available results on maps (results)
        places = self.driver.find_elements(By.CLASS_NAME, class_name)
        longitude = []
        latitude = []
        name = []
        
        for place in places:
            
            # Filter in the url latitude and longitude (closed between the !3d and !4d characters)
            geographic_loc = re.findall("\!3d(-?\d+\.\d+)\!4d(-?\d+\.\d+)",
                                        place.get_attribute(loc_attribute))[0]
            
            latitude.append(geographic_loc[0])
            longitude.append(geographic_loc[1])
            name.append(place.get_attribute(name_attribute))
            
        return {"latitude":latitude, "longitude":longitude, "name":name}
            
    def GetResultsReviews(self, parent_class_name:str, 
                          class_name:str, name_attribute:str="aria-label") -> dict:
        
        '''
        
        This function retrieves the general metrics (reviews) of the google map search
        
        Parameters
        ----------
        
        parent_class_name: str
            Common class name of the parent node where would be expected the HMTL of the review.
            Not all the results on google maps have reviews and this argument is thought to
            deal with that
        
        class_name: str
            Common class name of the HTML where is located the review info
            
        name_attribute: str
            common attribute name to find the info about the review. name_attribute is expected
            to be found in class_name
        
        Return
        ------
        
        dict: number of comments and general rating of the results of the search
        
        
        '''
        
        # Retrieving all available results on maps (reviews)
        reviews = self.driver.find_elements(By.CLASS_NAME, parent_class_name)
        n_comments = []
        rating = []
        
        for review in reviews:
            
            check_review = review.find_elements(By.CLASS_NAME, class_name)
            
            if len(check_review) > 0:
        
                review_cleaned = check_review[0].get_attribute(name_attribute) 
                review_cleaned = re.findall("(\d\.\d|\s+\d+)", review_cleaned)
        
                rating.append(review_cleaned[0])
                n_comments.append(review_cleaned[1].strip())
        
            else:
                rating.append(np.NaN)
                n_comments.append(np.NaN)
                
        return {"comments":n_comments, "rating": rating}


# In[26]:


def PipelineScrap(scrap_object, query, argument_dict):
    
    scrap_object.SearchByUrl(query, argument_dict["xpath_search_buttom"])
    
    scrap_object.ScrollDownResults(argument_dict["xpath_element_results"],
                                   argument_dict["class_name_results"])
    
    # Defining if there are zero results or partial match
    scrap_object.DefineSearchStatus(argument_dict["class_name_results"],
                                    argument_dict["class_name_partial_coincidence"])
    
    if scrap_object.zero_results_status or scrap_object.partial_match_status:
        
        warnings.warn(f"Zero results or partial match was found. Skiping {scrap_object.url}")
        return({"latitude":[], "longitude":[], "name":[]}, {"comments":[], "rating":[]})
    
    locations = scrap_object.GetResultsLocation(class_name = argument_dict["class_name_results"])
    reviews = scrap_object.GetResultsReviews(parent_class_name = argument_dict["parent_class_name_reviews"], 
                                            class_name = argument_dict["class_name_reviews"])
    
    return locations, reviews


# In[27]:


def ConvertMarks(text:str):
    
    '''
    Converts vowel accents found in Spanish to their base form
    '''
    
    base_form_vowels = {"á":"a","é":"e","í":"i","ó":"o","ú":"u"}
    new_string = ""
    
    for character in text:
        
        if character in base_form_vowels.keys():
            new_string += base_form_vowels[character]
        else:
            new_string += character
    
    return new_string


# In[33]:

if __name__ == "__main__":

    # First argument specifies in how many parts will be splitted the zip codes list
    # Second argument specifies what part of the splitted zip code list will be used (start=0)
    args = list(map(int, sys.argv[1:]))


    # In[29]:


    # Getting Delegaciones from a web table
    delegaciones_cdmx = pd.read_html("https://micodigopostal.org/ciudad-de-mexico/")
    delegaciones_cdmx = delegaciones_cdmx[0].drop(labels=4).values.reshape(-1,)


    # In[30]:


    # Parsing zip codes and metadata about zip codes from delegaciones
    delegaciones_cdmx_clean = [delegacion.lower().replace(" ","-") for delegacion in delegaciones_cdmx]

    # Replacing accent marks by its base form
    for i, delegacion in enumerate(delegaciones_cdmx_clean):
        delegaciones_cdmx_clean[i] = ConvertMarks(delegacion).replace(".","")

    # Creating url and retrieving from web zip codes in mexico city
    cdmx_address = pd.DataFrame()
    for url in delegaciones_cdmx_clean:
        web_page = f"https://micodigopostal.org/ciudad-de-mexico/{url}/"
        cdmx_address = pd.concat([cdmx_address, pd.read_html(web_page)[0]])


    # In[31]:


    # Cleaning unnecesary rows using the pattern "adsbygoogle"
    mask = map(lambda x: bool(re.findall("adsbygoogle", x)), cdmx_address["Asentamiento▼"])
    mask = pd.Series(list(mask))
    cdmx_address = cdmx_address[~mask.values].copy()


    # In[8]:


    zip_code = cdmx_address["Código Postal"].values
    zip_code = np.unique(zip_code)
    zip_code.sort()
    zip_code = np.array_split(zip_code, args[0])[args[1]]


    # In[9]:


    # Defining paths to scrap on maps
    web_driver_path = "/home/lromero/Descargas/chromedriver_linux64/chromedriver"

    # Search buttom to click
    xpath_search_buttom = '//*[@id="searchbox-searchbutton"]'

    # HTML elements on google maps when searching. Box element, individual results and partial match
    # repectively
    xpath_element_results = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]'
    class_name_results =  'hfpxzc'
    class_name_partial_coincidence = "L5xkq Hk4XGb".replace(" ", ".")

    # HTML for each result on maps and general reviews of those respectively
    parent_class_name_reviews = "UaQhfb fontBodyMedium".replace(" ", ".")
    class_name_reviews = "ZkP5Je"

    # Defining argument dict
    scrapping_arguments = {"xpath_search_buttom":xpath_search_buttom, 
                           "xpath_element_results":xpath_element_results,
                           "class_name_results":class_name_results,
                           "class_name_partial_coincidence":class_name_partial_coincidence,
                           "parent_class_name_reviews":parent_class_name_reviews,
                           "class_name_reviews":class_name_reviews}

    # Initialize scraping object
    google_maps_scrapper = ScrapMaps(web_driver_path, )

    oxxo_df = pd.DataFrame()
    start_block = time.time()

    for i, zp in enumerate(zip_code):

        start = time.time()
        query = f'oxxo postal code "{zp}"'
        url = "https://www.google.com/maps/search/" + query.replace(" ", "+") + "/"

        try:
            # google_maps_scrapper is modified inside the function (Passed by reference?)
            oxxo_loc, oxxo_rev = PipelineScrap(google_maps_scrapper, url,
                                                   scrapping_arguments)

        except:

            warnings.warn(f"Warning: NoSuchElementException error was found. Re-launching browser")

            # Re-launching browser if some element was not found
            google_maps_scrapper.driver.close()
            time.sleep(2)
            google_maps_scrapper = ScrapMaps(web_driver_path, 4)

            # google_maps_scrapper is modified inside the function (Passed by reference?)
            oxxo_loc, oxxo_rev = PipelineScrap(google_maps_scrapper, url,
                                                scrapping_arguments)


        oxxo_current_zip = pd.merge(left=pd.DataFrame(oxxo_loc), right=pd.DataFrame(oxxo_rev), 
                                    right_index=True, left_index=True)

        oxxo_current_zip["cp"] = str(zp)

        oxxo_df = pd.concat([oxxo_df, oxxo_current_zip])

        end = time.time()
        print(f"This iter took {end - start} secs")

        # Hopefully google dont ban me
        if ((i + 1) % 10) == 0:

            end_block = time.time()
            print("\t10 iterations have been completed. Waiting 5 seconds")
            print(f"\tThis block took {end_block - start_block} secs")
            start_block = time.time()

            oxxo_df.to_csv(f"oxxo_coordinates_{args[1]}.csv", index=False)

            time.sleep(5)

        if ((i + 1) % 100) == 0:
            print("\t100 iterations have been completed")

        # To keep a track of the current zip if all else fails to re-run cell from here
        zip_code = zip_code[1:]

    oxxo_df.to_csv(f"oxxo_coordinates_{args[1]}.csv", index=False)
    google_maps_scrapper.driver.close()