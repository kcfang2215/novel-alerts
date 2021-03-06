# Filename: novel_alerts_model.py

"""Model that runs operations on data that is fed in through the controller."""

# Import csv for reading, appending, and writing csv files
import csv
# Import smtplib and ssl for sending emails
import smtplib
import ssl
# Import callable to type annotate functions
from typing import Callable, Union
# Import requests and BeautifulSoup libraries to web scrape URL's
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup


class NovelAlertsModel:
    """
    A class that represents the model for the Model-View-Controller(MVC) design pattern.

    :param FIELD_NAMES: List of dict string key headings
    :type FIELD_NAMES: List[str]
    :param _URL_file_path: File path of URL data
    :type _URL_file_path: str
    :param EMAIL_FILE_PATH: File path of email data
    :type EMAIL_FILE_PATH: str
    :param _user_email: Users email
    :type _user_email: str
    :param _url_data: List of dictionaries in the format: {"URL": "url_Link, "latestChapter": "chapter"}
    :type _url_data: list[dict[str, str]]
    :param _password: users email password
    :type _password: str
    :param _message_box: GUI error msg method that brings up a message box
    :type _message_box: NovelAlertsView method
    """

    FIELD_NAMES = ["URL", "latestChapter"]

    def __init__(self, message_box: Callable=print, URL_path: str="data/URL_log.csv", email_path: str="data/email.txt") -> None:
        """Model Initializer"""

        self._URL_file_path = URL_path
        self._email_file_path = email_path
        self._user_email = self._load_email()
        self._url_data = self._load_URL_Data()
        self._password = ""
        self._message_box = message_box 
        
        # Initializes the csv file with column headers if there was no previous data.
        if not self._url_data:
            self._write_URL_data_to_file()

    # Add function that figures out which website is added and get call different versions of latest chapter functions
    def _get_Latest_Chapter_URL_Filtered(self, URL: str) -> Union[str, None]:
        """Choose a different version of the get latest chapter function by using the URL"""

        if "wln" in URL and "series-id" in URL: 
            return self._webscrape_WLN_Latest_Chapter(URL)
        elif "novelupdates" in URL and "series" in URL:
            return self._webscrape_Novelupdates_Latest_Chapter(URL)
        else:
            self._message_box("ERROR: URL is not correct or from wlnupdates or novelupdates domain")

    def _webscrape_WLN_Latest_Chapter(self, URL: str) -> Union[str, None]:
        """Web scrapes the latest chapter from the URL link and must be from domain https://www.wlnupdates.com/"""

        try:
            # Title: How to Web Scrape using Beautiful Soup in Python without running into HTTP error 403
            # Author: Raiyan Quaium
            # Availability: https://medium.com/@raiyanquaium/how-to-web-scrape-using-beautiful-soup-in-python-without-running-into-http-error-403-554875e5abed

            # Requests the URL data with disguised headers 
            req = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
            # Opens the url and reads the html as a string
            webpage = urlopen(req).read()
            # Creates Bs4 object with arguments consisting of html to be parsed and which parser to use.
            page_soup = soup(webpage, "html.parser")
            # Uses the soup object to find 'h5' tags within the html
            # .text is used to grab the text within the tag and nothing else.
            # [17:] is used to splice the text string to not include "Latest release - "
            # Ex. <h5>Latest release - vol 2.0  chp. 351.0</h5>
            latest_chapter = page_soup.find("h5").text[17:]
            return latest_chapter
        except Exception:
            # Returns None if latest chapter could not be found
            self._message_box("ERROR: Could not find the latest chapter and was not entered into the data.")

    def _webscrape_Novelupdates_Latest_Chapter(self, URL: str) -> Union[str, None]:
        """Web scrapes the latest chapter from the URL link and must be from domain https://www.novelupdates.com/"""

        try:
            req = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
            webpage = urlopen(req).read()
            page_soup = soup(webpage, "html.parser")
            # Uses the soup object to find all 'a' tags with the class 'chp-release'
            # Uses the bracket to access the first result which is the latest chp
            # .text is used to grab the text within the tag and nothing else.
            # Ex. <a class="chp-release" href="someLink.com"> text </a>
            latest_chapter = page_soup.findAll("a", "chp-release")[0].text
            return latest_chapter
        except Exception:
            self._message_box("ERROR: Could not find the latest chapter and was not entered into the data.")

    def _integrate_Updated_URLS(self, updated_URLS: list[str]) -> str:
        """Integrate updated urls into a string"""

        message = """"""

        for url in updated_URLS:
            message += f"""{url}\n"""

        return message

    def _send_Email(self, updated_URLS: list[str]) -> None:
        """Sends a email to user with a list of URL's that have new updates"""

        # Title: Sending Emails with Python
        # Author: Joska de Langen
        # Availability: https://realpython.com/python-send-email/

        # For SSL
        port = 465 

        message = self._integrate_Updated_URLS(updated_URLS)

        # default context validates host name, certificates, and optimizes security of connection
        context = ssl.create_default_context()

        try:
            # Initiates a TLS-encrypted connection
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                try:
                    server.login(self._user_email, self._password)
                    server.sendmail(self._user_email, self._user_email, message)
                except Exception:
                    self._message_box("ERROR: Email or password is incorrect!")
        except Exception:
            self._message_box("ERROR: Server connection could not be established!")

    def _compile_updated_URLS(self) -> list[str]:
        """Compiles a list of updated URLS by comparing current chapters with new chapters"""

        updated_URLS = []
        for dict_ in self._url_data:
            # Gets the latestchapter and compare it to the current one in object
            # If it is less than the latest chapter then append URL to list of updated URL's and set new chapter into object
            # No need to check for None from function call because webscraping the URL has worked if it is already in data structure.
            latest_chapter = self._get_Latest_Chapter_URL_Filtered(dict_[self.FIELD_NAMES[0]])
            if latest_chapter == None:
                continue

            if dict_[self.FIELD_NAMES[1]] < latest_chapter:
                updated_URLS.append(dict_[self.FIELD_NAMES[0]])
                dict_[self.FIELD_NAMES[1]] = latest_chapter

        return updated_URLS

    def _webscrape_Check(self) -> Union[int, None]:
        """Check if there are new updates and sends that data to _send_Email"""

        if self._url_data:
            try:
                updated_URLS = self._compile_updated_URLS()
        
                # If there were new updated novels
                if updated_URLS:
                    # write the new latest chapter data into the csv file.
                    self._write_URL_data_to_file()
                    self._send_Email(updated_URLS)
            except Exception:
                self._message_box("Error: Webscraper did not work. If this continues then restart program.")

    def setEmail(self, email: str) -> None:
        """Set the new email and saves it to email file"""

        self._user_email = email

        with open(self._email_file_path, "w") as email_file:
            email_file.write(self._user_email)

    def _load_email(self) -> str:
        """Loads the email from email file into class property"""

        with open(self._email_file_path, "r") as email_file:
            return email_file.read()

    def getEmail(self) -> str:
        """Returns email of the user"""

        return self._user_email
    
    def setPassword(self, password: str) -> None:
        """Set the password"""

        self._password = password

    def getPassword(self) -> str:
        """Gets the password"""

        return self._password

    def _load_URL_Data(self) -> list[dict[str, str]]:
        """Opens csv file to be read into a list of dictionarys"""

        with open(self._URL_file_path, mode='r') as csv_file:
            reader = csv.DictReader(csv_file)
            return list(map(dict, reader))

    def addURLData(self, URL: str) -> None:
        """Add the new URL to the dictionary and csv file"""

        for dict_ in self._url_data:
            if dict_["URL"] == URL:
                self._message_box("ERROR: URL is already in data structure")
                return
        
        # Gets the latest chapter and if return type is None, then function call did not get latest chapter and doesn't add it to data.
        latest_chapter = self._get_Latest_Chapter_URL_Filtered(URL)
        if latest_chapter == None: 
            return
        
        dict_row = {self.FIELD_NAMES[0]: URL, self.FIELD_NAMES[1]: latest_chapter}

        self._url_data.append(dict_row)

        with open(self._URL_file_path, mode='a') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.FIELD_NAMES)
            writer.writerow(dict_row)

    def _get_URL_data(self) -> list[dict[str, str]]:
        """Gets the current URL data within the object"""
        return self._url_data

    def _set_URL_data(self, URL_data: list[dict[str, str]]) -> None:
        """Sets the URL data to the object and file"""
        self._url_data = URL_data
        self._write_URL_data_to_file()

    def _write_URL_data_to_file(self) -> None:
        """Writes current object _url_data into the csv file"""

        with open(self._URL_file_path, mode='w') as csv_file:
            # DictWriter object that allows for file output with dictionary keys as fieldnames/columns/headers
            writer = csv.DictWriter(csv_file, fieldnames=self.FIELD_NAMES)

            writer.writeheader()
            for dict_ in self._url_data:
                writer.writerow(dict_)

    def deleteURLData(self, URL: str) -> None:
        """Delete the URL from the class object and rewrite data into the csv file """

        for dict_ in self._url_data:
            if dict_[self.FIELD_NAMES[0]] == URL:
                self._url_data.remove(dict_)
                self._message_box("Success")
                self._write_URL_data_to_file()
                return
        
        # Calls msgBox because URL data has been iterated through and match was not found
        self._message_box("Error: URL is not within existing data or not correct!")
