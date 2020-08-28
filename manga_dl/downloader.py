import requests
from bs4 import BeautifulSoup
from lxml import html
import os
import sys
import urllib.request
from abc import ABC, abstractmethod
import shutil
from manga_dl.manga_exceptions import *



"""
+~~~~~~~~~~~~~~~~~~~~+
| MangaReaderScraper |
+~~~~~~~~~~~~~~~~~~~~+

Performs GET request to find search results for manga series provided,
and downloads every page associated with the chapter provided (if valid chapter #).

This class can automatically create a local directory in which to store the image files
if it doesn't already exist:

Example layout:

./
 └───series
     └───dragon-ball-super
         └───1
             └───pages

"""


class MangaReaderScraper:
    
    # Class name identifier for search results
    CLS_NAME_SEARCH_RESULT = "d57"
    # Class name identifier for unordered list containing latest chapters.
    CLS_NAME_UL_LATEST_CHAPTER = "d44"
    # User agent header
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                             '50.0.2661.102 Safari/537.36'}

    def __init__(self, url="https://www.mangareader.net", series=None, chapter=1):
        self.url = url
        self.chapter_url = f"{url}/{series}/{chapter}"
        self.img_link = None
        self.series = series
        self.chapter = chapter
        self._list_of_series = []
    
       
    # Performs search and updates series name    
    def get_list_of_series(self):
        try:
            # Search for series
            url_search = f"https://www.mangareader.net/search/?nsearch={self.series.lower()}&msearch="        
            # Send get request to page
            response = requests.get(url_search, headers=self.headers)
            # Create soup object, which will help parse html
            soup = BeautifulSoup(response.text, "html.parser")
            # Get the first search result
            results = soup.find_all("div", class_= self.CLS_NAME_SEARCH_RESULT)

            # If a match is found, provide results.
            if results:
                # Create list of search results
                list_of_results = [i.find("a")["href"][1:] for i in results]
                # set search results to property
                self._list_of_series = list_of_results

            else:
                raise InvalidSeriesProvided

        except InvalidSeriesProvided:
            print('Unable to find series. Please check the series name you have provided and try again.')



    # Retrieves/downloads all pages for a chapter of a manga provided on MangaReader.net
    def get_pages(self, current_page=1):
        
        try:
            # Perform initial request to ensure series name is valid. If so, create directory
            init_request = requests.get(f"{self.url}/{self.series}", headers=self.headers)
            # Update directory path if status code is OK.
            if init_request.status_code == 200:
                # Update local directory to store new series/chapter
                self.update_path()
                print('Attempting to download chapter now.')
            else:
                raise BadStatusCodeError
            
            # Reset image link attribute if there was a prior error and the same chapter is selected.
            self.img_link = None

            while True:

                # Send get request to page
                response = requests.get(f"{self.get_chapter_url}/{current_page}", headers=self.headers)
                # Create soup object, which will help parse html
                soup = BeautifulSoup(response.text, "html.parser")
                # Get current image
                current_page_img = soup.find("img", id="ci")["src"]
                # If the image url has not changed, break loop
                if current_page_img == self.img_link:
                    print(f'Chapter {self.chapter} has finished downloading.')
                    break
                else:
                    # Set img_link attribute
                    self.img_link = current_page_img
                    # download file using scraped image element url
                    self.download_img('http:' + current_page_img, current_page)
                    # iterate
                    current_page += 1
                    # continue loop
                    continue

                 

        # Occurs on initial GET request to validate series selection
        except BadStatusCodeError:
            raise BadStatusCodeError('Unable to find series on server. Please try again later.')  
        # If unknown server error occurs                    
        except StatusCode520Error:
            raise StatusCode520Error('Unexpected server issue has occurred. Please try again later.')
        # If server times out on GET request for page image.
        except StatusCode522Error:
            raise StatusCode522Error('Server timeout on GET request for Chapter %s, Page %s. Please try again later.' % (self.chapter, current_page))
        # If invalid series is provided.
        except InvalidSeriesProvided:
            raise InvalidSeriesProvided("Invalid series name provided.")
        # Invalid chapter provided
        except TypeError:
            raise TypeError("Chapter provided for this series does not exist. Please try again.")
        # If file that is attempting to be removed or modified is open.
        except PermissionError:
            raise PermissionError("Attempted to modify path that is currently open! Please close any related " 
                  "files that are open and try again.")
        # For unexpected exceptions
        except Exception as e:
            raise Exception(f'An unexpected error has occurred. {e}')

    # Ensures that a file path is made for series/chapter
    def update_path(self):

        # Create main series folder if it does not exist
        if not os.path.exists("series"):
            # create series directory
            self.add_series_folder()

        # Create folder path to specific series, if it doesn't already exist
        if not os.path.exists(f"series/{self.series}"):
            # add name of series to path
            self.add_series_dir()

        # If the chapter exists within directory
        if os.path.exists(f"series/{self.series}/{self.chapter}"):
            # Notify that the chapter exists within directory and is being removed.
            print('Chapter already exists. Removing.')
            # Remove chapter and contents from directory
            shutil.rmtree(f"series/{self.series}/{self.chapter}")

        # Add chapter and pages to directory
        self.add_chapter_and_page_dir()

    """
    get_number_of_chapters:

    Searches for the latest chapter element in the unordered list
    for 'Latest Chapters', and retrieves the chapter number from
    the 'href' attribute of that link.

    """

    def get_number_of_chapters(self):
        try:
            # create url to search directly for series selected.
            url_to_search = f"{self.url}/{self.series}"
            # Perform initial request to ensure series name is valid. If so, create directory
            series_search = requests.get(f"{url_to_search}", headers=self.headers)
            # Update directory path if status code is OK.
            if series_search.status_code == 200:
                soup = BeautifulSoup(series_search.text, "html.parser")             
                latest_chapter = [i.find("a")["href"] for i in soup.find(name="ul", class_=self.CLS_NAME_UL_LATEST_CHAPTER)][0].split('/')[-1]
                return latest_chapter
            else:
                raise BadStatusCodeError
        except BadStatusCodeError:
            print('Server issue has occurred. Please try again later.')
        # Print status code error
        except Exception as e:
            print(f'An unexpected error has occurred. {e}')
                
    # Get raw content of request and download manga page
    def download_img(self, image_url, page):
        # file_format
        img_format = image_url.split('.')[-1]
        # path to download before replacing file name
        file_path = os.path.join(os.getcwd(), f"series\\{self.series}\\{self.chapter}\\pages\\{page}.{img_format}")
        # send get request
        r = requests.get(image_url, stream=True)

        # print(r.status_code)

        # If server times out
        if r.status_code == 522:
            raise StatusCode522Error
        # If server reaches an unexpected error.
        if r.status_code == 520:
            raise StatusCode520Error

        # if response status is successful
        if r.status_code == 200:
            # get raw attribute of reponse
            r.raw_decode_content = True 
            # Open file in manga's 'pages' file path
            with open(file_path, 'wb') as f:
                # copy file to path
                shutil.copyfileobj(r.raw, f)
           # notify of successful download
            print(f"Chapter {self.chapter} Page {page} downloaded.")
    
    # Checks if string is valid integer
    @staticmethod
    def is_integer(val: str):
        try:
            int(val)
            return True
        except ValueError:
            return False
    # If folder series does not exist, add it
    @staticmethod
    def add_series_folder():
        os.mkdir("series")
    # Adds series to directory
    def add_series_dir(self):
        os.mkdir(f"series/{self.series}")
    # Adds chapter and pages to directory
    def add_chapter_and_page_dir(self):
        os.mkdir(f"series/{self.series}/{self.chapter}")
        os.mkdir(f"series/{self.series}/{self.chapter}/pages")

    @property
    def list_of_series(self):
        return self._list_of_series
    @property
    def get_chapter_url(self):
        return f"{self.url}/{self.series}/{self.chapter}"
    def has_a_single_result(self):
        return len(self._list_of_series) > 0



        
        


            



        




            
    

