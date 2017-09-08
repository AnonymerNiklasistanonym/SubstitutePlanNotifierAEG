# -*- coding: utf-8 -*-

#!/bin/env python3
"""
This script scraps a table from a specific website, writes it in json format to the file system
and sends an email to the recipients.
"""

# My imports (the crawler)
import json
import re
import logging
import datetime
import os
import requests
from bs4 import BeautifulSoup

# Gmail Imports (not important for the actual crawler)
from SimplifiedGmailApiSubmodule.SendGmailSimplified import SimplifiedGmailApi


# Paths for important directories and files - from home directory
HOME_DIR = os.path.expanduser('~')

# change this to the directory your script is: !!!!!!!!!!!!!!!!!
DIR_OF_SCRIPT = os.path.join(HOME_DIR, os.path.join("Documents", "SubstitutePlanNotifierAEG"))
# "Documents"
# "Documents/GitHubBeta"

PATH_FOR_LOG = os.path.join(DIR_OF_SCRIPT, "script.log")

DIRECTORY_FOR_TABLES = os.path.join(DIR_OF_SCRIPT, 'tables')
DIRECTORY_FOR_DATA = os.path.join(DIR_OF_SCRIPT, 'data')

PATH_FOR_WEBSITES = os.path.join(DIRECTORY_FOR_DATA, 'websites.json')
PATH_FOR_HTML_FILE = os.path.join(DIRECTORY_FOR_DATA, 'html.json')


# Setup the Gmail API - set USE_GMAIL False if you want to use the Simplified Gmail API
USE_GMAIL = True
if USE_GMAIL:
    DIR_OF_GMAIL_API_FILES = os.path.join(DIR_OF_SCRIPT, os.path.join("SimplifiedGmailApiSubmodule", "gmail_api_files"))
    PATH_OF_CLIENT_DATA = os.path.join(DIR_OF_GMAIL_API_FILES, "client_data.json")
    PATH_OF_CLIENT_SECRET = os.path.join(DIR_OF_GMAIL_API_FILES, "client_secret.json")
    GmailServer = SimplifiedGmailApi(PATH_OF_CLIENT_DATA, PATH_OF_CLIENT_SECRET, DIR_OF_GMAIL_API_FILES)
else:
    GmailServer = None


# Check if the directory for the tables exists, if not create it
if not os.path.exists(DIRECTORY_FOR_TABLES):
    os.makedirs(DIRECTORY_FOR_TABLES)

# load all websites and recipients
with open(PATH_FOR_WEBSITES, "r") as websites_file:
    websites = json.load(websites_file)
    numberOfWebsites = len(websites)
# load json with all html information
with open(PATH_FOR_HTML_FILE, "r") as html_file:
    html_data = json.load(html_file)

# log file
logging.basicConfig(filename=PATH_FOR_LOG, level=logging.DEBUG)


def extract_important_information(html_table):
    """Clean the list strings.

    Remove the not important characters, spacwes, newlines, ecetera.

    Args:
    table_data: list of html extracted table

    Returns:
        List with only the important data.
    """

    # for every row
    for a in range(len(html_table)):
        # remove the first column (class id)
        del html_table[a][0]
        for b in range(len(html_table[a])):
            new_text = html_table[a][b]
            # remove newlines and more
            new_text = "".join(new_text.split("-\n"))
            new_text = "".join(new_text.split("\n"))
            new_text = "".join(new_text.split("\r"))
            # remove spaces (https://stackoverflow.com/a/21484372/7827128)
            new_text = re.sub(r"^\s*(-\s*)?|(\s*-)?\s*$", "", new_text)
            # special thing (German: "H. to Hour")
            new_text = "Stunde".join(new_text.split("Std."))
            html_table[a][b] = new_text

            if b > 2:
                if not html_table[a][3]:
                    html_table[a][b] = ""

    return html_table


def create_html_message(json_table, class_url, email_date_string):
    """Create the HTML email.

    Args:
    table_data: clean list of html extracted table
    class_url: url of website

    Returns:
        The complete Html email as a String.
    """

    html_message = html_data["head"]
    html_message += html_data["title-body"]
    html_message += html_data["top"]
    html_message += email_date_string
    html_message += html_data["top2"]

    # convert Json list to a custom and clean html table
    for a in range(1, len(json_table)):
        html_message += html_data["tr-start"]
        if not json_table[a][3]:
            for b in range(len(json_table[a])):
                html_message += html_data["td-start"] + html_data["strike-start"]
                if b < 3:
                    html_message += json_table[a][b]
                else:
                    html_message += "---"
                html_message += html_data["strike-end"] + html_data["td-end"]
        else:
            for b in range(len(json_table[a])):
                html_message += html_data["td-start"]
                html_message += json_table[a][b]
                html_message += html_data["td-end"]
        html_message += html_data["tr-end"]
    html_message += html_data["middle"]
    html_message += class_url
    html_message += html_data["space-between-link-and-text"]
    html_message += html_data["linktext-plan"]
    html_message += html_data["bottom"]
    html_message += html_data["bottom-text-01"]
    html_message += html_data["bottom-text-space-01"]
    html_message += html_data["bottom-text-02"]
    html_message += html_data["bottom-text-space-02"]
    html_message += html_data["bottom-text-03"]
    html_message += html_data["bottom-text-space-03"]
    html_message += html_data["bottom-text-04"]
    html_message += html_data["end"]

    # html_message.encode('us-ascii', 'ignore')
    html_message.encode('ascii', 'xmlcharrefreplace')

    return html_message


def compare_lists(old_list, new_list):
    """Compare the two lists.

    Args:
    old_list: old clean list of extracted Html table
    new_list: new clean list of extracted Html table

    Returns:
        Are they different (True) or not (False) as a boolean.
    """

    print("old list:")
    print(old_list)
    print("new list:")
    print(new_list)
    if old_list is None:
        message_old_list = str(old_list)
    else:
        message_old_list = ''.join(map(str, old_list))
    logging.debug("old list: " + message_old_list)
    if new_list is None:
        message_new_list = str(new_list)
    else:
        message_new_list = ''.join(map(str, new_list))
    logging.debug("new list: " + message_new_list)

    # check if there is even an new list
    if new_list is None:
        print("new_list is None")
        logging.info("No change because of: new list is None")
        return False

    # check if there was even an old list
    if old_list is None:
        print("old_list is None")
        logging.info("Change because of: old list is None and new list is not None")
        # at this point we know, that the new table isn't empty
        return True

    # check if one list is bigger than the other
    if len(old_list) != len(new_list):
        # not "not is" but "!=" is used because it doesn't work after 256:
        # https://stackoverflow.com/questions/2239737/is-it-better-to-use-is-or-for-number-comparison-in-python
        print("len(old_list) " + str(len(old_list)) + " is not len(new_list) " + str(len(new_list)))
        logging.info("Change because of: old list (" + str(len(old_list)) + ") and new list (" + str(len(new_list))
                     + ") have different lengths")
        return True

    # if they are the same size iterate over them to find a difference
    for a in range(1, len(new_list)):
        for b in range(len(new_list[a])):
            if new_list[a][b] is not old_list[a][b]:
                print("new_list[a][b]:" + new_list[a][b] + " and old_list[a][b]: " + old_list[a][b])
                logging.info("Change because of: at [" + str(a) + "][" + str(b) + "] old list is \"" +
                             old_list[a][b] + "\" and new list is \"" + new_list[a][b] + "\"")
                return True

    # or not - they must be the same
    logging.info("No change because of: old list and new list are the same")
    return False


# get time - https://stackoverflow.com/a/43302976/7827128
date_time = datetime.datetime.now()
date = date_time.date()  # gives date
time = date_time.time()  # gives time

# zfill adds leading zeros if number length is below parameter - https://stackoverflow.com/a/733478/7827128
date_string = str(date.year) + "." + str(date.month).zfill(2) + "." + str(date.day).zfill(2)
time_string = str(time.hour).zfill(2) + ":" + str(time.minute).zfill(2) + ":" + str(time.second).zfill(2)

logging.info("script started on " + date_string + " at " + time_string)


#    logging.info('So should this')
#    logging.warning('And this, too')

# check if there are any websites
if numberOfWebsites > 0:

    # for every website get table
    for x in websites:

        print(">> Check for the class " + x["name"] + ":")
        logging.info("check the website " + x["url"] + " for the class " + x["name"])

        # try to get it in the first place
        try:
            # get website
            res = requests.get(x["url"])
            content = res.content

            print(content)
            # extract the second table
            soup = BeautifulSoup(content, 'html.parser')
            email_date_string = str(soup.find_all('b')[2].get_text()).replace("Vertretungsplan Klassen", "").lstrip(" ")

            #soup = BeautifulSoup(content, 'html.parser')
            table = soup.find_all('table')[1]
            # remove tags and create list(https://stackoverflow.com/a/18544794/7827128)
            table_data = [[cell.text for cell in row("td")] for row in table("tr")]
            print("Extracted table from " + x["url"] + ":")
            print(table_data)
            # extract the important information from the list
            table_data = extract_important_information(table_data)
            # convert table to JSON format
            new_json_table = (json.dumps(table_data))

            # try to read latest version from filesystem
            try:
                test = os.stat(DIRECTORY_FOR_TABLES + "/" + x["name"] + ".json")
                with open(DIRECTORY_FOR_TABLES + "/" + x["name"] + ".json", "r") as savedTable_file:
                    old_json_table = json.load(savedTable_file)
                    # convert the extracted JSON to a JSON (for comparison)
                    old_json_table = (json.dumps(old_json_table))
            # when the file doesn't exists set it to None
            except os.error:
                old_json_table = None
                logging.warning("The file " + DIRECTORY_FOR_TABLES + "/" + x["name"] + ".json was not found")

        # this error comes up when there is no Website
        except IndexError:
            new_json_table, old_json_table = None, None
            print("Website could not be crawled!")
            logging.warning("The website " + x["url"] + "could not be crawled")
        # More catches thanks to https://stackoverflow.com/a/16511493/7827128
        except requests.exceptions.HTTPError as e:
            new_json_table, old_json_table = None, None
            # http error (414, etc.)
            logging.warning(e)
        except requests.exceptions.Timeout as e:
            new_json_table, old_json_table = None, None
            # Maybe set up for a retry, or continue in a retry loop
            logging.warning(e)
        except requests.exceptions.TooManyRedirects as e:
            new_json_table, old_json_table = None, None
            # Tell the user their URL was bad and try a different one
            logging.warning(e)
        except requests.exceptions.RequestException as e:
            new_json_table, old_json_table = None, None
            # catastrophic error. bail.
            logging.warning(e)

        # if there is no old file, a new one, that is different to the old one continue
        if compare_lists(old_json_table, new_json_table):

            # 1. save new table as json file
            with open(DIRECTORY_FOR_TABLES + "/" + x["name"] + ".json", 'w') as file:
                json.dump(table_data, file)
                logging.debug("the file " + DIRECTORY_FOR_TABLES + "/" + x["name"] +
                              ".json was successfully overwritten with the new list")

            # 2. send it to all recipients an email with the change
            if USE_GMAIL and GmailServer is not None:

                subject = "Neuer Vertretungsplan Klasse " + x["name"]

                message_text = create_html_message(table_data, x["url"], email_date_string)

                message_text = re.sub(r'[^\x00-\x7F]+', ' ', message_text)

                print("Message:")
                print(message_text.encode('ascii', 'xmlcharrefreplace').decode('ascii'))
                print("send to")

                for y in x["recipients"]:
                    if GmailServer.send_html(y, subject, message_text):
                        logging.info(">> Email was successfully sent to " + y)
                    else:
                        logging.debug(">> Email was not sent to " + y)

        else:
            print("no changes to the class " + x["name"])
