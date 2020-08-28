from manga_dl.downloader import MangaReaderScraper
from tkinter import (Tk, Button, messagebox,
                     Entry, Toplevel, Listbox, Label,
                     Scrollbar, Frame, ttk)
import time
import threading                   

# Icon path used for each window
ICON_PATH = 'manga_dl/resources/luffy_flag.ico'


class BaseWindow(Toplevel):
    def __init__(self, title: str):
        # call parent
        super().__init__()
        # set window position
        self.geometry("+300+300")
        # Prevent resizing of window
        self.resizable(width=False, height=False)
        # set title
        self.title(title)
        # frame object
        self.frame = Frame(self)


class BaseListMenu(BaseWindow):
    def __init__(self, title: str):
        # call parent object
        super().__init__(title=title)
        # scrollbar
        self.scrollbar = Scrollbar(self.frame, orient="vertical")



class LoadingBar(object):
    call_ms = 60
    def __init__(self, func):
        
        self.root = Tk()
        self.root.iconbitmap(ICON_PATH)
        self.root.title('Downloading...')
        self.root.geometry("+300+300")

        self.msg_label = Label(self.root, text='Downloading file, please wait...')
        self.msg_label.pack(pady=10)

        self.progbar = ttk.Progressbar(self.root)
        self.progbar.config(maximum=4, mode='indeterminate')
        self.progbar.pack(pady=10)
        
        self.start_thread(func)
        self.root.mainloop()


    def start_thread(self, func):
        self.progbar.start()
        self.secondary_thread = threading.Thread(target=func)
        self.secondary_thread.start()
        self.root.after(self.call_ms, self.check_thread)

    def check_thread(self):
        if self.secondary_thread.is_alive():
            self.root.after(self.call_ms, self.check_thread)
        else:
            self.progbar.stop()
            self.root.destroy()


class ChapterListWindow(BaseListMenu):
    # Window title
    TITLE = 'Chapter Results'

    def __init__(self, prior_window, manga_scraper_obj: MangaReaderScraper):
        # call parent object
        super().__init__(title=self.TITLE)
        # set scraper attribute
        self.scraper = manga_scraper_obj
        # listbox
        self.list_box = Listbox(self.frame, width=50, selectmode='single', yscrollcommand=self.scrollbar.set)
        # add data to listbox
        total_no_chapters = self.scraper.get_number_of_chapters()
        # Add each chapter number to list box
        [self.list_box.insert('end', i) for i in range(1, int(total_no_chapters) + 1)]
        # default selection to first index
        self.list_box.select_set(0)
        # set scrollbar view to listbox
        self.scrollbar.config(command=self.list_box.yview)
        # pack scrollbar
        self.scrollbar.pack(side='right', fill='y')
        # set default icon
        self.iconbitmap(ICON_PATH)
        # pack frame
        self.frame.pack()
        # pack list box
        self.list_box.pack(pady=15)
          
        # inner method for retrieving chapter image files
        def get_chapter(self, chapter_chosen):
            try:
                                
                # Update chapter attribute
                self.scraper.chapter = chapter_chosen       
                # Download image
                LoadingBar(func=self.scraper.get_pages)

            except Exception as e:
                messagebox.showerror(title='ERROR', message=e)
            finally:
                return
        

        # OK Button
        self.ok_btn = Button(self, text='OK', command=lambda: get_chapter(self, chapter_chosen=self.list_box.selection_get()))
        self.ok_btn.pack(side='left', padx=(80,10), pady=10)

        # closes the current window and restores focus to the prior open window (in this instance, the series results)
        def close_and_restore_focus(self, prior_window):
            self.destroy()
            prior_window.focus_force()
            prior_window.grab_set()

        # Cancel Button
        self.cancel_btn = Button(self, text='Cancel', command=lambda: close_and_restore_focus(self, prior_window))
        self.cancel_btn.pack(side='right', padx=(10,80), pady=10) 

class SearchResultsWindow(BaseListMenu):

    # Window title
    TITLE = 'Search Results'

    def __init__(self, manga_scraper_obj: MangaReaderScraper):
        # call parent
        super().__init__(title=self.TITLE)
        # listbox
        self.list_box = Listbox(self.frame, width=50, selectmode='single', yscrollcommand=self.scrollbar.set)
        # add data to listbox
        self.list_box.insert('end', *manga_scraper_obj.list_of_series)
        # default selection to first index
        self.list_box.select_set(0)
        # set scrollbar view to listbox
        self.scrollbar.config(command=self.list_box.yview)
        # pack scrollbar
        self.scrollbar.pack(side='right', fill='y')
        # set default icon
        self.iconbitmap(ICON_PATH)
        # pack frame
        self.frame.pack()
        # pack list box
        self.list_box.pack(pady=15)

        # inner method for when ok button is clicked
        def ok_btn_click(self, manga_scraper_obj, series_chosen):
            self.check(manga_scraper_obj, series_chosen)

        # OK Button
        self.ok_btn = Button(self, text='OK', command=lambda: ok_btn_click(self, manga_scraper_obj=manga_scraper_obj, series_chosen=self.list_box.selection_get()))
        self.ok_btn.pack(side='left', padx=(80,10), pady=10)

        # Cancel Button
        self.cancel_btn = Button(self, text='Cancel', command=lambda: self.destroy())
        self.cancel_btn.pack(side='right', padx=(10,80), pady=10) 

    def check(self, manga_scraper_obj, series_chosen):
        if series_chosen is not None:
            # Set series attribute for manga scraper
            manga_scraper_obj.series = series_chosen
            # Initialize chapter list window
            chapter_results = ChapterListWindow(prior_window=self, manga_scraper_obj=manga_scraper_obj)
            chapter_results.focus_force()
            self.grab_release()            
            chapter_results.grab_set()

        else:
            # Notify that a series hasn't been selected yet.
            messagebox.showinfo(title='Please select', message='No series selected.')



class MainMenu(Tk):
    # Window title
    TITLE = 'MangaReader Download'

    def __init__(self):
        # call parent
        super().__init__()
        # set icon
        self.iconbitmap(ICON_PATH)
        # # set window position
        self.geometry("+300+300")
        # add frame
        self.frame = Frame(self)
        # add bottom frame
        self.bottom_frame = Frame(self)
        # set title
        self.title(self.TITLE)
        # Prevent resizing of window
        self.resizable(width=False, height=False)
        # Label: search manga
        self.manga_entry_lbl = Label(self.frame, text="Manga series:")
        # Add label to grid
        self.manga_entry_lbl.pack(side='left', padx=20, pady=10)
        # search entry field
        self.manga_entry = Entry(self.frame)
  
        # add entry to grid
        self.manga_entry.pack(side='left', fill='x', padx=20, pady=10)        
        # search button
        self.search_btn = Button(self.bottom_frame, text="Search", height=1, width=6, 
                     command=self.search_results)
        # add search button to grid
        self.search_btn.pack(side='bottom', pady=10)
        # pack frame object
        self.frame.pack()
        # pack bottom frame object
        self.bottom_frame.pack(side='bottom')

    # Open search results window
    def search_results(self):        
        if self.manga_entry is not None: 
            # Create scraper object
            m = MangaReaderScraper(url="https://www.mangareader.net", series=self.manga_entry.get(), chapter=1)
            # sets manga list property
            m.get_list_of_series()
            # Checks if there are no search results
            if not m.has_a_single_result():
                messagebox.showwarning(title='No results found', message='Sorry, unable to find any results.')
                return
            # Create window
            search_results = SearchResultsWindow(m)
            search_results.focus_force()
            search_results.grab_set()