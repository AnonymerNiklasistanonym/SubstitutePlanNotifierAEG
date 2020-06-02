# -*- coding: utf-8 -*-

#!/bin/env python3
"""
This script scraps a table from a specific website, writes it in json format to the file system
and sends an email to the recipients.
"""

import datetime
import json
import logging
import os
import re

import requests
from bs4 import BeautifulSoup

# Gmail Imports (not important for the actual crawler)
from SimplifiedGmailApiSubmodule.SendGmailSimplified import SimplifiedGmailApi


# Paths for important directories and files - from home directory
HOME_DIR = os.path.expanduser('~')

# change this to the directory your script is: !!!!!!!!!!!!!!!!!
DIR_OF_SCRIPT = os.path.join(HOME_DIR, os.path.join("Documents",
                                                    "SubstitutePlanNotifierAEG"))
# "Documents"
# "Documents/GitHubBeta"

PATH_FOR_LOG = os.path.join(DIR_OF_SCRIPT, "script.log")

DIRECTORY_FOR_TABLES = os.path.join(DIR_OF_SCRIPT, 'tables')
DIRECTORY_FOR_DATA = os.path.join(DIR_OF_SCRIPT, 'data')

PATH_FOR_WEBSITES = os.path.join(DIRECTORY_FOR_DATA, 'websites.json')
PATH_FOR_HTML_FILE = os.path.join(DIRECTORY_FOR_DATA, 'html.json')


# Setup the Gmail API - set USE_GMAIL False if you want to use the Simplified Gmail API
USE_GMAIL = False
if USE_GMAIL:
    DIR_OF_GMAIL_API_FILES = os.path.join(
        DIR_OF_SCRIPT, os.path.join("SimplifiedGmailApiSubmodule", "gmail_api_files"))
    PATH_OF_CLIENT_DATA = os.path.join(
        DIR_OF_GMAIL_API_FILES, "client_data.json")
    PATH_OF_CLIENT_SECRET = os.path.join(
        DIR_OF_GMAIL_API_FILES, "client_secret.json")
    GMAIL_SERVER = SimplifiedGmailApi(
        PATH_OF_CLIENT_DATA, PATH_OF_CLIENT_SECRET, DIR_OF_GMAIL_API_FILES)
else:
    GMAIL_SERVER = None


# Check if the directory for the tables exists, if not create it
if not os.path.exists(DIRECTORY_FOR_TABLES):
    os.makedirs(DIRECTORY_FOR_TABLES)

# load all websites and recipients
with open(PATH_FOR_WEBSITES, "r") as websites_file:
    WEBSITES_JSON_DATA = json.load(websites_file)
    NUMBER_OF_ALL_WEBSITES = len(WEBSITES_JSON_DATA)
# load json with all html information
with open(PATH_FOR_HTML_FILE, "r") as html_file:
    HTML_DATA = json.load(html_file)

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
    for row, _ in enumerate(html_table):
        # remove the first column (class id)
        del html_table[row][0]
        for column, val in enumerate(html_table[row]):
            new_text = val
            # remove newlines and more
            new_text = "".join(new_text.split("-\n"))
            new_text = "".join(new_text.split("\n"))
            new_text = "".join(new_text.split("\r"))
            # remove spaces (https://stackoverflow.com/a/21484372/7827128)
            new_text = re.sub(r"^\s*(-\s*)?|(\s*-)?\s*$", "", new_text)
            # special thing (German: "H. to Hour")
            new_text = "Stunde".join(new_text.split("Std."))
            html_table[row][column] = new_text

            if column > 2:
                if not html_table[row][3]:
                    html_table[row][column] = ""

    return html_table


def create_html_message(json_table, class_url, date_and_week):
    """Create the HTML email.

    Args:
    table_data: clean list of html extracted table
    class_url: url of website

    Returns:
        The complete Html email as a String.
    """

    html_message = HTML_DATA["head"]
    html_message += HTML_DATA["title-body"]
    html_message += HTML_DATA["top"]
    html_message += date_and_week
    html_message += HTML_DATA["top2"]

    # convert Json list to a custom and clean html table
    for row in range(1, len(json_table)):
        html_message += HTML_DATA["tr-start"]
        # check if something doesn't take place (check [3] = room = '')
        if not json_table[row][3]:
            for column, val in enumerate(json_table[row]):
                # Strike everything but the hour
                if column != 0:
                    html_message += HTML_DATA["td-start"] + HTML_DATA["strike-start"]
                    # catch an empty descripton/room
                    if val == "":
                        # and add '---' for a better readability
                        html_message += "---"
                    else:
                        html_message += val
                else:
                    html_message += HTML_DATA["td-start"] + val
                html_message += HTML_DATA["strike-end"] + HTML_DATA["td-end"]
        else:
            for column, val in enumerate(json_table[row]):
                html_message += HTML_DATA["td-start"]
                html_message += val
                html_message += HTML_DATA["td-end"]
        html_message += HTML_DATA["tr-end"]
    html_message += HTML_DATA["middle"]
    html_message += class_url
    html_message += HTML_DATA["space-between-link-and-text"]
    html_message += HTML_DATA["linktext-plan"]
    html_message += HTML_DATA["bottom"]
    html_message += HTML_DATA["bottom-text-01"]
    html_message += HTML_DATA["bottom-text-space-01"]
    html_message += HTML_DATA["bottom-text-02"]
    html_message += HTML_DATA["bottom-text-space-02"]
    html_message += HTML_DATA["bottom-text-03"]
    html_message += HTML_DATA["bottom-text-space-03"]
    html_message += HTML_DATA["bottom-text-04"]
    html_message += HTML_DATA["end"]

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
        logging.info("Change because of: old list (" + str(len(old_list)) + ") and new list ("
                     + str(len(new_list)) + ") have different lengths")
        return True

    # if they are the same size iterate over them to find a difference
    for row in range(1, len(new_list)):
        for column, val in enumerate(new_list[row]):
            if val is not old_list[row][column]:
                print("new_list[a][b]:" + val + " and old_list[a][b]: "
                      + old_list[row][column])
                logging.info("Change because of: at [" + str(row) + "][" + str(column)
                             + "] old list is \"" + old_list[row][column]
                             + "\" and new list is \"" + val + "\"")
                return True

    # or not - they must be the same
    logging.info("No change because of: old list and new list are the same")
    return False


# get time - https://stackoverflow.com/a/43302976/7827128
DATE_TIME = datetime.datetime.now()
DATE = DATE_TIME.date()  # gives date
TIME = DATE_TIME.time()  # gives time

# zfill adds leading zeros if number length is below parameter
# https://stackoverflow.com/a/733478/7827128
DATE_STRING = str(DATE.year) + "." + str(DATE.month).zfill(2) + "." + str(DATE.day).zfill(2)
TIME_STRING = str(TIME.hour).zfill(2) + ":" + str(TIME.minute).zfill(2) + ":" + str(
    TIME.second).zfill(2)

logging.info("script started on " + DATE_STRING + " at " + TIME_STRING)


#    logging.info('So should this')
#    logging.warning('And this, too')

# check if there are any websites
if NUMBER_OF_ALL_WEBSITES > 0:

    # for every website get table
    for WEBSITE_JSON_DATA in WEBSITES_JSON_DATA:

        print(">> Check for the class " + WEBSITE_JSON_DATA["name"] + ":")
        logging.info("check the website " + WEBSITE_JSON_DATA["url"] + " for the class "
                     + WEBSITE_JSON_DATA["name"])

        # try to get it in the first place
        try:
            # get website
            res = requests.get(WEBSITE_JSON_DATA["url"])
            content = res.content

            print(content)
            # extract the second table
            SOUP_HTML_DATA = BeautifulSoup(content, 'html.parser')

            # extract the date and the week number
            email_date_string = str(SOUP_HTML_DATA.find_all('b')[2].get_text())
            # remove a String and all whitespaces at the begin and the end
            email_date_string = email_date_string.replace("Vertretungsplan Klassen", "").lstrip(" ")

            #soup = BeautifulSoup(content, 'html.parser')
            table = SOUP_HTML_DATA.find_all('table')[1]
            # remove tags and create list(https://stackoverflow.com/a/18544794/7827128)
            table_data = [[cell.text for cell in row("td")] for row in table("tr")]
            print("Extracted table from " + WEBSITE_JSON_DATA["url"] + ":")
            print(table_data)
            # extract the important information from the list
            table_data = extract_important_information(table_data)
            # convert table to JSON format
            JSON_DATA_TABLE_NEW = (json.dumps(table_data))

            # try to read latest version from filesystem
            try:
                test = os.stat(DIRECTORY_FOR_TABLES + "/" + WEBSITE_JSON_DATA["name"] + ".json")
                with open(DIRECTORY_FOR_TABLES + "/" + WEBSITE_JSON_DATA["name"] + ".json",
                          "r") as savedTable_file:
                    # convert the extracted JSON to a JSON (for comparison)
                    JSON_DATA_TABLE_OLD = (json.dumps(json.load(savedTable_file)))
            # when the file doesn't exists set it to None
            except os.error:
                JSON_DATA_TABLE_OLD = None
                logging.warning("The file " + DIRECTORY_FOR_TABLES + "/" + WEBSITE_JSON_DATA["name"]
                                + ".json was not found")

        # this error comes up when there is no Website
        except IndexError:
            JSON_DATA_TABLE_NEW, JSON_DATA_TABLE_OLD = None, None
            print("Website could not be crawled!")
            logging.warning("The website " + WEBSITE_JSON_DATA["url"] + "could not be crawled")
        # More catches thanks to https://stackoverflow.com/a/16511493/7827128
        except requests.exceptions.HTTPError as exception1:
            JSON_DATA_TABLE_NEW, JSON_DATA_TABLE_OLD = None, None
            # http error (414, etc.)
            logging.warning(exception1)
        except requests.exceptions.Timeout as exception2:
            JSON_DATA_TABLE_NEW, JSON_DATA_TABLE_OLD = None, None
            # Maybe set up for a retry, or continue in a retry loop
            logging.warning(exception2)
        except requests.exceptions.TooManyRedirects as exception3:
            JSON_DATA_TABLE_NEW, JSON_DATA_TABLE_OLD = None, None
            # Tell the user their URL was bad and try a different one
            logging.warning(exception3)
        except requests.exceptions.RequestException as exception4:
            JSON_DATA_TABLE_NEW, JSON_DATA_TABLE_OLD = None, None
            # catastrophic error. bail.
            logging.warning(exception4)

        # if there is no old file, a new one, that is different to the old one continue
        if compare_lists(JSON_DATA_TABLE_OLD, JSON_DATA_TABLE_NEW):

            # 1. save new table as json file
            with open(DIRECTORY_FOR_TABLES + "/" + WEBSITE_JSON_DATA["name"] + ".json",
                      'w') as file:
                json.dump(table_data, file)
                logging.debug("the file " + DIRECTORY_FOR_TABLES + "/" + WEBSITE_JSON_DATA["name"] +
                              ".json was successfully overwritten with the new list")

            # 2. send it to all recipients an email with the change
            if USE_GMAIL and GMAIL_SERVER is not None:

                SUBJECT = "Neuer Vertretungsplan Klasse " + WEBSITE_JSON_DATA["name"]

                MESSAGE_TEXT = create_html_message(table_data, WEBSITE_JSON_DATA["url"],
                                                   email_date_string)

                #print("Message:")
                #print(MESSAGE_TEXT.encode('ascii', 'xmlcharrefreplace').decode('ascii'))
                print(" >>> Send messages:")

                for RECIPIENT in WEBSITE_JSON_DATA["recipients"]:
                    if GMAIL_SERVER.send_html(RECIPIENT, SUBJECT, MESSAGE_TEXT):
                        logging.info(">> Email was successfully sent to " + RECIPIENT)
                    else:
                        logging.debug(">> Email was not sent to " + RECIPIENT)

        else:
            print("no changes to the class " + WEBSITE_JSON_DATA["name"])
