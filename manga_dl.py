import requests
from bs4 import BeautifulSoup
from lxml import html
import os
import sys
import urllib.request
from abc import ABC, abstractmethod
import shutil

# Exception raised if user provides a series name that is not valid on MangaReader.net.

class InvalidSeriesProvided(Exception):
    pass

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

class MangaReaderScraper(ABC):
    
    # Class name identifier for search results
    CLS_NAME_FIRST_SEARCH_RESULT = "d57"
    # User agent header
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                             '50.0.2661.102 Safari/537.36'}

    @abstractmethod
    def __init__(self, url, series, chapter):
        self.url = url
        self.chapter_url = f"{url}/{series}/{chapter}"
        self.img_link = None
        self.series = series
        self.chapter = chapter
    
    # Performs search and updates series name    
    def search_series(self):
        try:
            # Search for series
            url_search = f"https://www.mangareader.net/search/?nsearch={self.series.lower()}&msearch="        
            # Send get request to page
            response = requests.get(url_search, headers=self.headers)
            # Create soup object, which will help parse html
            soup = BeautifulSoup(response.text, "html.parser")
            # Get the first search result
            results = soup.find_all("div", class_= self.CLS_NAME_FIRST_SEARCH_RESULT)

            # If a match is found, provide results.
            if results:
                # Create list of search results
                list_of_results = [i.find("a")["href"][1:] for i in results]
                # If there is more than one search result, prompt to choose which to pick.
                if len(list_of_results) > 1:
                    # Print each item of search results
                    print('Search results')
                    for i in range(len(list_of_results)):
                        print("%s: %s" % (str(i), list_of_results[i]))
                    
                    while True:
                        # store input which will dictate which series to choose from
                        series_to_choose = input('Choose from above results.\n').replace(' ', '')
                        # checks if input is valid
                        if self.is_integer(series_to_choose):
                            if int(series_to_choose) in range(0, len(list_of_results)-1):
                                break
                            else:
                                print('Selection out of range.')
                                continue
                        else:
                            print('Invalid selection chosen.')
                            continue 

                else:
                    # default to first index
                    series_to_choose = 0
                    print('One result found.')
                # update series to url representation
                self.series = list_of_results[int(series_to_choose)]
                # reset chapter url
                self.chapter_url = f"{self.url}/{self.series}/{self.chapter}"

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
                self.update_path()
                print('Attempting to download chapter now.')
            else:
                raise requests.HTTPError

            while True:

                # Send get request to page
                response = requests.get(f"{self.chapter_url}/{current_page}", headers=self.headers)
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

        # Print status code error
        except requests.HTTPError as httpError:
            print(httpError)
            return
        # If invalid series is provided.
        except InvalidSeriesProvided:
            print("Invalid series name provided.")
            return
        # Invalid chapter provided
        except TypeError:
            print("Chapter provided for this series does not exist. Please try again.")
            return
        # If file that is attempting to be removed or modified is open.
        except PermissionError:
            print("Attempted to modify path that is currently open! Please close any related " 
                  "files that are open and try again.")            
            return
        except Exception as e:
            print(f'An unexpected error has occurred. {e}')
            return

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

    # Get raw content of request and download manga page
    def download_img(self, image_url, page):
        # file_format
        img_format = image_url.split('.')[-1]
        # path to download before replacing file name
        file_path = os.path.join(os.getcwd(), f"series\\{self.series}\\{self.chapter}\\pages\\{page}.{img_format}")
        # send get request
        r = requests.get(image_url, stream=True)
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


# Inherits from MangaReaderScraper

class MangaChapter(MangaReaderScraper):
    def __init__(self, url="https://www.mangareader.net", series="dragonball", chapter=1):
        super().__init__(url, series, chapter)
    def get_chapters(self):
        # TODO: Allow ability to download multiple chapters.
        pass
    

def main(series_name, chapter):
    o = MangaChapter(series=series_name, chapter=chapter)  # Instantiate scraper class   
    o.search_series()                                      # Validate series name provided
    o.get_pages()                                          # Download chapter pages


if __name__ == '__main__':
    stop_dl = False
    while not stop_dl:
        series_name = input('Enter a manga series:\n')
        chapter = input('Enter a chapter:\n')    
        main(series_name, chapter)

        response = ''
        while response not in ['y', 'n']:
            response = input('Would you like to continue? (y/n)\n').strip().lower()      
            if response in ['y','n']:
                if response == 'n':
                    stop_dl = True
                break
            else:
                print('Invalid input')
                continue


        
        


            



        




            
    

