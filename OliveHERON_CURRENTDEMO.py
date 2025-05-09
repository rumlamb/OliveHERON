import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import sys
import requests
from bs4 import BeautifulSoup
import webbrowser
from pathlib import Path
from better_profanity import profanity
import zipfile
import re
import threading

# --- OliveHERON Theme Configuration ---
OLIVE = "#708238"
OLIVE_DARK = "#556B2F"
OLIVE_LIGHT = "#BFCF87"
RETRO_BROWN = "#2B1B0E"
RETRO_TAN = "#F5EEDC"
RETRO_ACCENT = "#B3A369"
RETRO_ACCENT2 = "#C5B358"
FONT = ("Courier New", 11, "bold")
ICON_FONT = ("Arial", 18, "bold")  # For 𓆂 symbol

SUPPORTED_EXTENSIONS = [
    'epub', 'pdf', 'mobi', 'azw3', 'txt', 'html', 'zip', 'jpg', 'jpeg', 'png',
    'gif'
]

SUPPORTED_OPERATIONS = [
    'filename= (or just enter text)', 'author=', 'title=', 'language=',
    'ext= (epub, pdf, mobi, azw3, txt, html, zip, jpg, png, gif)', 'source=',
    'uploader=', 'upload_date=', 'upload_date:before=', 'upload_date:after=',
    'file_age=', 'publishdate=', 'publishdate:range=', 'isbn=', 'intext:',
    'allintext:', 'AROUND(n): AROUND(n) ', 'daterange:', 'hits:',
    'wildcard (*)', 'quoted phrases ("...")',
    'AND, OR, parentheses for grouping'
]

SORTING_OPTIONS = [
    'filename/title', 'author', 'language', 'source/site', 'uploader name',
    'upload date', 'file age', 'publish date', 'hits'
]

settings = {
    'dark_mode': True,
    'default_search_ops': '',
    'excluded_filters': '',
    'filter_explicit': True,
    'show_welcome': True,
    'show_features': True,
    'default_download_dir': str(Path.home() / "Downloads"),
    'default_app': '',
    'per_ext_app': {},
    'user_searchbases': []
}

SETTINGS_FILE = "oliveheron_settings.txt"
custom_download_dir = None  # Session override


def get_download_dir():
    if custom_download_dir:
        return Path(custom_download_dir)
    if settings.get('default_download_dir'):
        return Path(settings['default_download_dir'])
    if "ANDROID_STORAGE" in os.environ or sys.platform == "android":
        return Path("/sdcard/Download/")
    else:
        return Path.home() / "Downloads"


def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            for k, v in settings.items():
                if k == "per_ext_app" or k == "user_searchbases":
                    f.write(f"{k}={repr(v)}\n")
                else:
                    f.write(f"{k}={v}\n")
    except Exception as e:
        print("Settings save error:", e)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    if k == "per_ext_app" or k == "user_searchbases":
                        try:
                            settings[k] = eval(v)
                        except:
                            settings[k] = {} if k == "per_ext_app" else []
                    elif v.lower() in ("true", "false"):
                        settings[k] = v.lower() == "true"
                    else:
                        settings[k] = v
    except Exception as e:
        print("Settings load error:", e)


def get_theme():
    if settings['dark_mode']:
        return {
            'bg': RETRO_BROWN,
            'fg': OLIVE_LIGHT,
            'accent': OLIVE,
            'accent2': RETRO_ACCENT,
            'entry_bg': OLIVE_DARK,
            'entry_fg': OLIVE_LIGHT,
            'tree_bg': RETRO_BROWN,
            'tree_fg': OLIVE_LIGHT,
            'tree_alt': OLIVE_DARK,
            'tree_sel_bg': OLIVE_DARK,
            'tree_sel_fg': OLIVE_LIGHT,
            'tree_head_bg': OLIVE,
            'tree_head_fg': OLIVE_LIGHT,
            'button_bg': OLIVE,
            'button_fg': RETRO_BROWN,
            'ribbon_bg': OLIVE,
            'ribbon_fg': OLIVE_LIGHT,
        }
    else:
        return {
            'bg': RETRO_TAN,
            'fg': RETRO_BROWN,
            'accent': OLIVE,
            'accent2': RETRO_ACCENT2,
            'entry_bg': OLIVE_LIGHT,
            'entry_fg': RETRO_BROWN,
            'tree_bg': RETRO_TAN,
            'tree_fg': RETRO_BROWN,
            'tree_alt': OLIVE_LIGHT,
            'tree_sel_bg': OLIVE_LIGHT,
            'tree_sel_fg': RETRO_BROWN,
            'tree_head_bg': OLIVE,
            'tree_head_fg': RETRO_TAN,
            'button_bg': OLIVE,
            'button_fg': RETRO_TAN,
            'ribbon_bg': OLIVE,
            'ribbon_fg': RETRO_TAN,
        }


def themed_popup(title,
                 message,
                 buttons,
                 checkbox_text=None,
                 checkbox_var=None,
                 scrollable=False):
    popup = tk.Toplevel()
    popup.title(title)
    popup.geometry("600x600")
    popup.configure(bg=get_theme()['bg'])
    popup.transient()
    popup.grab_set()

    # Optional: scrollable text
    if scrollable:
        frame = tk.Frame(popup, bg=get_theme()['bg'])
        frame.pack(expand=True, fill='both', padx=10, pady=10)
        text = tk.Text(frame,
                       wrap='word',
                       bg=get_theme()['entry_bg'],
                       fg=get_theme()['entry_fg'],
                       font=FONT)
        text.insert('1.0', message)
        text.config(state='disabled')
        text.pack(side='left', expand=True, fill='both')
        scrollbar = tk.Scrollbar(frame, command=text.yview)
        scrollbar.pack(side='right', fill='y')
        text.config(yscrollcommand=scrollbar.set)
    else:
        label = tk.Label(popup,
                         text=message,
                         bg=get_theme()['bg'],
                         fg=get_theme()['fg'],
                         font=FONT,
                         justify='left',
                         anchor='w')
        label.pack(padx=10, pady=10, expand=True, fill='both')

    if checkbox_text and checkbox_var is not None:
        cb = tk.Checkbutton(popup,
                            text=checkbox_text,
                            variable=checkbox_var,
                            bg=get_theme()['bg'],
                            fg=get_theme()['fg'],
                            font=FONT)
        cb.pack(pady=(0, 10))

    def on_button(cmd=None):
        popup.grab_release()
        popup.destroy()
        if cmd:
            cmd()

    for (text, cmd) in buttons:
        btn = tk.Button(popup,
                        text=text,
                        command=lambda c=cmd: on_button(c),
                        bg=get_theme()['button_bg'],
                        fg=get_theme()['button_fg'],
                        font=FONT)
        btn.pack(side='left', padx=10, pady=10)

    popup.wait_window()


def show_tutorial():
    features_var = tk.BooleanVar(
        value=not settings.get('show_features', True) == False)

    def set_show_features():
        settings['show_features'] = not features_var.get()
        save_settings()

    tutorial_text = (
        "Welcome to OliveHERON!\n\n"
        "OliveHERON is a retro-themed, cross-platform e-book search and download tool. "
        "You can search for books by title, author, extension, ISBN, and more. "
        "Results are pulled from Project Gutenberg, Anna's Archive, LibGen, Standard Ebooks, Internet Archive, Rave Book Search, and any custom searchbases you add in Settings.\n\n"
        "HERONSearch Guide:\n"
        "- Enter a simple search (e.g. 'menswear') or use advanced operators:\n"
        " • author=augustine\n"
        " • filename=confessions\n"
        " • ext=epub\n"
        " • isbn=9780385029551\n"
        " • publishdate=1960\n"
        " • publishdate:range=1950-1960\n"
        " • upload_date=2020-01-01\n"
        " • upload_date:before=2022-01-01\n"
        " • upload_date:after=2019-01-01\n"
        " • file_age=30 (days)\n"
        " • source=LibGen\n"
        " • intext:sin\n"
        " • allintext:prayer hope\n"
        " • hits:5 (limit results)\n"
        " • wildcard: use * as a wildcard (e.g. 'augustine of hi*')\n"
        " • quoted: use \"...\" for exact phrases (e.g. \"what does love look like?\")\n"
        " • AROUND(n): e.g. 'poor AROUND(3) needy'\n"
        " • daterange:2020-01-01,2022-12-31\n"
        " • AND, OR, parentheses for grouping: (augustine of hippo OR Aurelius Augustinus Hipponensis ) AND \"it has eyes to see misery and want.\"\n"
        "\n"
        "EXAMPLES:\n"
        " author=tolkien ext=epub hits:3\n"
        " \"harry potter\" OR \"lord of the rings\"\n"
        " publishdate:range=1950-1970 AND magic\n"
        " intext:dragon AROUND(5) knight\n"
        " source=LibGen upload_date:after=2021-01-01\n"
        " isbn=9780261103573\n"
        "\n"
        "WHAT DO THESE MEAN?\n"
        "- upload_date: when a file was added to a database\n"
        "- file_age: how old the file is (in days)\n"
        "- publishdate: year the book was published (from metadata)\n"
        "- source: which database/site to search (e.g. LibGen, Internet Archive)\n"
        "- AROUND(n): finds two words within n words of each other\n"
        "- hits: limits the number of results\n"
        "- daterange: restricts by upload or publish date\n"
        "- ISBN: searches by ISBN (if available)\n"
        "- intext: term must appear in the text\n"
        "- allintext: all terms must appear in the text\n"
        "- AND, OR, parentheses: combine queries\n"
        "\n"
        "SETTINGS:\n"
        "- Change between Dark/Light mode\n"
        "- Set your default downloads folder\n"
        "- Choose which app opens files by default, or set apps per file extension (Advanced)\n"
        "- Add custom searchbases (websites) to include in your search\n"
        "- Enable/disable explicit content filtering (profanity, mature, adult, etc)\n"
        "- Toggle whether Welcome/Tutorial popups appear on startup\n"
        "\n"
        "DOWNLOADING:\n"
        "- Select a file and click 'Download Selected'.\n"
        "- Select multiple files for batch download (as zip or individually).\n"
        "- Use 'Save to...' to pick a custom download folder for this session.\n"
        "\n"
        "Enjoy OliveHERON!\n"
        "\n"
        "Supported search operations and metadata fields:\n")

    for op in SUPPORTED_OPERATIONS:
        tutorial_text += f"- {op}\n"

    tutorial_text += "\nSorting options:\n"
    for op in SORTING_OPTIONS:
        tutorial_text += f"- {op}\n"

    themed_popup(title="TUTORIAL",
                 message=tutorial_text,
                 buttons=[("OK", set_show_features)],
                 checkbox_text="Do not show again",
                 checkbox_var=features_var,
                 scrollable=True)


# --- Scraper Functions for Each Source ---


def scrape_gutenberg(query, results, lock, filter_explicit):
    url = f"https://www.gutenberg.org/ebooks/search/?query={requests.utils.quote(query)}"
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select(".booklink")
        for row in rows:
            title = row.select_one(".title").get_text(strip=True)
            author = row.select_one(".subtitle")
            author = author.get_text(strip=True) if author else ""
            year = ""
            ext = "epub"
            src = "Gutenberg"
            link = "https://www.gutenberg.org" + row.find("a")["href"]
            if filter_explicit and profanity.contains_profanity(title + " " +
                                                                author):
                continue
            with lock:
                results.append((title, author, year, ext, src, link))
    except Exception as e:
        print("Gutenberg error:", e)


def scrape_ravebooksearch(query, results, lock, filter_explicit):
    # Uses Google's CSE, so parsing is similar to Google Custom Search results
    search_url = f"https://ravebooksearch.com/index.html?q={requests.utils.quote(query)}"
    try:
        resp = requests.get(search_url,
                            timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for result in soup.select('.gsc-webResult.gsc-result'):
            title_elem = result.select_one('.gs-title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            link = title_elem['href'] if title_elem and title_elem.has_attr(
                'href') else ""
            author = ""
            year = ""
            ext = ""
            src = "RaveBookSearch"
            if filter_explicit and profanity.contains_profanity(title):
                continue
            with lock:
                results.append((title, author, year, ext, src, link))
    except Exception as e:
        print("RaveBookSearch error:", e)


def scrape_annas_archive(query, results, lock, filter_explicit):
    # Anna's Archive meta-search
    search_url = f"https://annas-archive.org/search?q={requests.utils.quote(query)}"
    try:
        resp = requests.get(search_url,
                            timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select('.search-result'):
            title_elem = row.select_one('.search-result-title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            author_elem = row.select_one('.search-result-authors')
            author = author_elem.get_text(strip=True) if author_elem else ""
            year_elem = row.select_one('.search-result-pubyear')
            year = year_elem.get_text(strip=True) if year_elem else ""
            ext_elem = row.select_one('.search-result-format')
            ext = ext_elem.get_text(strip=True) if ext_elem else ""
            link_elem = row.select_one('a')
            link = "https://annas-archive.org" + link_elem[
                'href'] if link_elem and link_elem.has_attr('href') else ""
            src = "Anna's Archive"
            if filter_explicit and profanity.contains_profanity(title + " " +
                                                                author):
                continue
            with lock:
                results.append((title, author, year, ext, src, link))
    except Exception as e:
        print("Anna's Archive error:", e)


def scrape_libgen(query, results, lock, filter_explicit):
    # LibGen (fiction) search
    search_url = f"http://libgen.rs/fiction/?q={requests.utils.quote(query)}"
    try:
        resp = requests.get(search_url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find('table', {'class': 'catalog'})
        if not table:
            return
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) < 9:
                continue
            title = cols[2].get_text(strip=True)
            author = cols[1].get_text(strip=True)
            year = cols[4].get_text(strip=True)
            ext = cols[8].get_text(strip=True)
            link = cols[2].find('a')['href'] if cols[2].find('a') else ""
            src = "LibGen"
            if filter_explicit and profanity.contains_profanity(title + " " +
                                                                author):
                continue
            with lock:
                results.append((title, author, year, ext, src, link))
    except Exception as e:
        print("LibGen error:", e)


def scrape_internet_archive(query, results, lock, filter_explicit):
    search_url = f"https://archive.org/search.php?query={requests.utils.quote(query)}"
    try:
        resp = requests.get(search_url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select('.item-ia'):
            title_elem = row.select_one('.C234')
            title = title_elem.get_text(strip=True) if title_elem else ""
            author = ""
            year = ""
            ext = ""
            link_elem = row.select_one('a')
            link = "https://archive.org" + link_elem[
                'href'] if link_elem and link_elem.has_attr('href') else ""
            src = "Internet Archive"
            if filter_explicit and profanity.contains_profanity(title):
                continue
            with lock:
                results.append((title, author, year, ext, src, link))
    except Exception as e:
        print("Internet Archive error:", e)


def scrape_standard_ebooks(query, results, lock, filter_explicit):
    search_url = f"https://standardebooks.org/ebooks?query={requests.utils.quote(query)}"
    try:
        resp = requests.get(search_url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select('.book'):
            title_elem = row.select_one('.title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            author_elem = row.select_one('.author')
            author = author_elem.get_text(strip=True) if author_elem else ""
            year = ""
            ext = "epub"
            link_elem = row.find('a')
            link = "https://standardebooks.org" + link_elem[
                'href'] if link_elem and link_elem.has_attr('href') else ""
            src = "Standard Ebooks"
            if filter_explicit and profanity.contains_profanity(title + " " +
                                                                author):
                continue
            with lock:
                results.append((title, author, year, ext, src, link))
    except Exception as e:
        print("Standard Ebooks error:", e)


def scrape_user_searchbases(query, results, lock, filter_explicit):
    for base in settings.get('user_searchbases', []):
        try:
            url = base.format(query=requests.utils.quote(query))
            resp = requests.get(url, timeout=15)
            with lock:
                results.append((url, "", "", "", "User", url))
        except Exception as e:
            print("User searchbase error:", e)


class SettingsDialog(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("Settings")
        self.configure(bg=get_theme()['bg'])
        self.transient(master)
        self.grab_set()

        self.dark_mode_var = tk.BooleanVar(value=settings['dark_mode'])
        self.filter_explicit_var = tk.BooleanVar(
            value=settings['filter_explicit'])
        self.show_welcome_var = tk.BooleanVar(value=settings['show_welcome'])
        self.show_features_var = tk.BooleanVar(value=settings['show_features'])
        self.default_download_dir_var = tk.StringVar(
            value=settings['default_download_dir'])

        row = 0
        tk.Checkbutton(self,
                       text="Dark Mode",
                       variable=self.dark_mode_var,
                       bg=get_theme()['bg'],
                       fg=get_theme()['fg'],
                       font=FONT).grid(row=row,
                                       column=0,
                                       sticky='w',
                                       padx=10,
                                       pady=5)
        row += 1
        tk.Checkbutton(self,
                       text="Filter Explicit Content",
                       variable=self.filter_explicit_var,
                       bg=get_theme()['bg'],
                       fg=get_theme()['fg'],
                       font=FONT).grid(row=row,
                                       column=0,
                                       sticky='w',
                                       padx=10,
                                       pady=5)
        row += 1
        tk.Checkbutton(self,
                       text="Show Welcome",
                       variable=self.show_welcome_var,
                       bg=get_theme()['bg'],
                       fg=get_theme()['fg'],
                       font=FONT).grid(row=row,
                                       column=0,
                                       sticky='w',
                                       padx=10,
                                       pady=5)
        row += 1
        tk.Checkbutton(self,
                       text="Show Tutorial",
                       variable=self.show_features_var,
                       bg=get_theme()['bg'],
                       fg=get_theme()['fg'],
                       font=FONT).grid(row=row,
                                       column=0,
                                       sticky='w',
                                       padx=10,
                                       pady=5)
        row += 1
        tk.Label(self,
                 text="Default Download Directory:",
                 bg=get_theme()['bg'],
                 fg=get_theme()['fg'],
                 font=FONT).grid(row=row,
                                 column=0,
                                 sticky='w',
                                 padx=10,
                                 pady=5)
        tk.Entry(self,
                 textvariable=self.default_download_dir_var,
                 width=40,
                 bg=get_theme()['entry_bg'],
                 fg=get_theme()['entry_fg'],
                 font=FONT).grid(row=row, column=1, padx=10, pady=5)
        tk.Button(self,
                  text="Browse",
                  command=self.browse_folder,
                  bg=get_theme()['button_bg'],
                  fg=get_theme()['button_fg'],
                  font=FONT).grid(row=row, column=2, padx=10, pady=5)
        row += 1

        tk.Label(self,
                 text="Custom Searchbases (URLs with {query}):",
                 bg=get_theme()['bg'],
                 fg=get_theme()['fg'],
                 font=FONT).grid(row=row,
                                 column=0,
                                 sticky='w',
                                 padx=10,
                                 pady=5)
        self.searchbases_text = tk.Text(self,
                                        width=60,
                                        height=4,
                                        bg=get_theme()['entry_bg'],
                                        fg=get_theme()['entry_fg'],
                                        font=FONT)
        self.searchbases_text.grid(row=row,
                                   column=1,
                                   columnspan=2,
                                   padx=10,
                                   pady=5)
        self.searchbases_text.insert(
            '1.0', "\n".join(settings.get('user_searchbases', [])))
        row += 1

        tk.Button(self,
                  text="Save",
                  command=self.save,
                  bg=get_theme()['button_bg'],
                  fg=get_theme()['button_fg'],
                  font=FONT).grid(row=row, column=0, padx=10, pady=10)
        tk.Button(self,
                  text="Cancel",
                  command=self.cancel,
                  bg=get_theme()['button_bg'],
                  fg=get_theme()['button_fg'],
                  font=FONT).grid(row=row, column=1, padx=10, pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.default_download_dir_var.set(folder)

    def save(self):
        settings['dark_mode'] = self.dark_mode_var.get()
        settings['filter_explicit'] = self.filter_explicit_var.get()
        settings['show_welcome'] = self.show_welcome_var.get()
        settings['show_features'] = self.show_features_var.get()
        settings['default_download_dir'] = self.default_download_dir_var.get()
        settings['user_searchbases'] = [
            line.strip()
            for line in self.searchbases_text.get('1.0', 'end').splitlines()
            if line.strip()
        ]
        save_settings()
        self.grab_release()
        self.destroy()
        messagebox.showinfo(
            "Settings",
            "Settings saved. Please restart OliveHERON to apply theme changes."
        )

    def cancel(self):
        self.grab_release()
        self.destroy()


class OliveHeronApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("OliveHERON")
        self.geometry("1100x650")
        self.configure(bg=get_theme()['bg'])
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.search_var = tk.StringVar()
        self.filter_explicit_var = tk.BooleanVar(
            value=settings.get('filter_explicit', True))
        self.results = []
        self.result_columns = [
            "Title", "Author", "Year", "Ext", "Source", "URL"
        ]

        self.create_widgets()
        if settings.get('show_features', True):
            self.after(300, show_tutorial)

    def create_widgets(self):
        theme = get_theme()

        # Search bar
        search_frame = tk.Frame(self, bg=theme['bg'])
        search_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(search_frame,
                 text="Search:",
                 font=FONT,
                 bg=theme['bg'],
                 fg=theme['fg']).pack(side='left')
        search_entry = tk.Entry(search_frame,
                                textvariable=self.search_var,
                                font=FONT,
                                bg=theme['entry_bg'],
                                fg=theme['entry_fg'],
                                width=60)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<Return>', lambda e: self.do_search())
        tk.Button(search_frame,
                  text="Search",
                  font=FONT,
                  bg=theme['button_bg'],
                  fg=theme['button_fg'],
                  command=self.do_search).pack(side='left', padx=5)
        tk.Button(search_frame,
                  text="Settings",
                  font=FONT,
                  bg=theme['button_bg'],
                  fg=theme['button_fg'],
                  command=self.open_settings).pack(side='right', padx=5)
        tk.Checkbutton(search_frame,
                       text="Filter Explicit",
                       variable=self.filter_explicit_var,
                       bg=theme['bg'],
                       fg=theme['fg'],
                       font=FONT,
                       command=self.toggle_explicit).pack(side='right', padx=5)

        # Results table
        columns = self.result_columns
        style = ttk.Style()
        style.configure("Treeview",
                        background=theme['tree_bg'],
                        fieldbackground=theme['tree_bg'],
                        foreground=theme['tree_fg'],
                        font=FONT)
        style.configure("Treeview.Heading",
                        background=theme['tree_head_bg'],
                        foreground=theme['tree_head_fg'],
                        font=FONT)
        self.tree = ttk.Treeview(self,
                                 columns=columns,
                                 show='headings',
                                 selectmode='extended')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180 if col != "URL" else 0, anchor='w')
        self.tree.pack(expand=True, fill='both', padx=10, pady=5)
        self.tree.bind('<Double-1>', self.open_selected)

        # Buttons
        btn_frame = tk.Frame(self, bg=theme['bg'])
        btn_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(btn_frame,
                  text="Download Selected",
                  font=FONT,
                  bg=theme['button_bg'],
                  fg=theme['button_fg'],
                  command=self.download_selected).pack(side='left', padx=5)
        tk.Button(btn_frame,
                  text="Open Selected",
                  font=FONT,
                  bg=theme['button_bg'],
                  fg=theme['button_fg'],
                  command=self.open_selected).pack(side='left', padx=5)
        tk.Button(btn_frame,
                  text="Save to...",
                  font=FONT,
                  bg=theme['button_bg'],
                  fg=theme['button_fg'],
                  command=self.choose_download_folder).pack(side='right',
                                                            padx=5)

    def do_search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showinfo("No Query", "Please enter a search query.")
            return
        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.after(
            100, lambda: threading.Thread(target=self.search_thread,
                                          args=(query, )).start())

    def search_thread(self, query):
        results = []
        lock = threading.Lock()
        threads = []
        filter_explicit = self.filter_explicit_var.get()
        threads.append(
            threading.Thread(target=scrape_gutenberg,
                             args=(query, results, lock, filter_explicit)))
        threads.append(
            threading.Thread(target=scrape_ravebooksearch,
                             args=(query, results, lock, filter_explicit)))
        threads.append(
            threading.Thread(target=scrape_annas_archive,
                             args=(query, results, lock, filter_explicit)))
        threads.append(
            threading.Thread(target=scrape_libgen,
                             args=(query, results, lock, filter_explicit)))
        threads.append(
            threading.Thread(target=scrape_internet_archive,
                             args=(query, results, lock, filter_explicit)))
        threads.append(
            threading.Thread(target=scrape_standard_ebooks,
                             args=(query, results, lock, filter_explicit)))
        threads.append(
            threading.Thread(target=scrape_user_searchbases,
                             args=(query, results, lock, filter_explicit)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.results = results
        self.after(0, self.show_results)

    def show_results(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.results:
            self.tree.insert('', 'end', values=row)

    def download_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select a file to download.")
            return
        for item in selected:
            vals = self.tree.item(item, "values")
            url = vals[-1]
            filename = vals[0].replace(
                " ", "_") + "." + (vals[3] if vals[3] else "epub")
            self.download_file(url, filename)

    def download_file(self, url, filename):
        folder = get_download_dir()
        filepath = folder / filename
        try:
            if "gutenberg.org" in url:
                book_id = re.search(r'/(\d+)', url)
                if book_id:
                    book_id = book_id.group(1)
                    epub_url = f"https://www.gutenberg.org/ebooks/{book_id}.epub.images"
                    r = requests.get(epub_url,
                                     allow_redirects=True,
                                     timeout=20)
                    if r.status_code == 404:
                        epub_url = f"https://www.gutenberg.org/ebooks/{book_id}.epub.noimages"
                        r = requests.get(epub_url,
                                         allow_redirects=True,
                                         timeout=20)
                    if r.status_code == 404:
                        epub_url = f"https://www.gutenberg.org/ebooks/{book_id}.epub"
                        r = requests.get(epub_url,
                                         allow_redirects=True,
                                         timeout=20)
                    if r.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(r.content)
                        messagebox.showinfo("Download Complete",
                                            f"Saved to {filepath}")
                        return
            webbrowser.open(url)
            messagebox.showinfo(
                "Redirected",
                "File opened in browser (direct download not available).")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))

    def open_selected(self, event=None):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select a file to open.")
            return
        for item in selected:
            vals = self.tree.item(item, "values")
            url = vals[-1]
            webbrowser.open(url)

    def choose_download_folder(self):
        global custom_download_dir
        folder = filedialog.askdirectory()
        if folder:
            custom_download_dir = folder
            messagebox.showinfo("Download Folder",
                                f"Session download folder set to:\n{folder}")

    def open_settings(self):
        SettingsDialog(self)

    def toggle_explicit(self):
        settings['filter_explicit'] = self.filter_explicit_var.get()
        save_settings()

    def on_exit(self):
        save_settings()
        self.destroy()


if __name__ == "__main__":
    profanity.load_censor_words()
    load_settings()
    app = OliveHeronApp()
    app.mainloop()
