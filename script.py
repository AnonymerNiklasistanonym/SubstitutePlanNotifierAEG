#!/bin/env python3
"""
This script scraps a table from a specific website, writes it in json format to the file system and sends an email to the recipients.
"""

# Gmail Imports (not important for the actual crawler)
from __future__ import print_function
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import base64
from email.mime.text import MIMEText
import os
from apiclient import errors

# My imports (the crawler)
import json
import requests
from bs4 import BeautifulSoup
import re
import logging
import datetime

# Paths for important directories and files - from home directory
HOME_DIR = os.path.expanduser('~')

# change this to the directory your script is: !!!!!!!!!!!!!!!!!
DIR_OF_SCRIPT = os.path.join(HOME_DIR, "Documents/SubstitutePlanNotifierAEG")
# "Documents/SimpleHtmlTableScraper")
# "Documents/GitHubBeta/BasicWebScraper/script_for_cron_scheduler")

PATH_FOR_LOG = os.path.join(DIR_OF_SCRIPT, "script.log")

DIRECTORY_FOR_TABLES = os.path.join(DIR_OF_SCRIPT, 'tables')
DIRECTORY_FOR_DATA = os.path.join(DIR_OF_SCRIPT, 'data')
#'data_real')
#'data')

DIRECTORY_FOR_GMAIL_API = os.path.join(DIRECTORY_FOR_DATA, '.credentials')
PATH_FOR_GMAIL_CREDENTIALS = os.path.join(DIRECTORY_FOR_DATA, 'gmail_credentials.json')

PATH_FOR_WEBSITES = os.path.join(DIRECTORY_FOR_DATA, 'websites.json')
PATH_FOR_HTML_FILE = os.path.join(DIRECTORY_FOR_DATA, 'html.json')

# Check if the directory for the tables exists, if not create it
if not os.path.exists(DIRECTORY_FOR_TABLES):
    os.makedirs(DIRECTORY_FOR_TABLES)

# load all websites and recipients + more data
with open(PATH_FOR_GMAIL_CREDENTIALS, "r") as credentials_file:
    moreData = json.load(credentials_file)
with open(PATH_FOR_WEBSITES, "r") as websites_file:
    websites = json.load(websites_file)
    numberOfWebsites = len(websites)
# load json with all html information
with open(PATH_FOR_HTML_FILE, "r") as html_file:
    html_data = json.load(html_file)

# log file
logging.basicConfig(filename = PATH_FOR_LOG, level = logging.DEBUG)


# Gmail API methods:

"""
If you want to implement the Gmail API read this first: https://developers.google.com/gmail/api/quickstart/python
You first need to activate the API over a Gmail account, then create OAuth client ID credentials and then
understand (run) the example because of the permission scopes (https://developers.google.com/gmail/api/auth/scopes).
"""

def SendMessage(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print ('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)
        return None

def CreateMessage(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    # message_text.encode('us-ascii', 'ignore').decode('us-ascii', 'ignore')

    message = MIMEText(message_text, 'html')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode())}

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    credential_dir = DIRECTORY_FOR_GMAIL_API
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# Gmail API (needs to be here)
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# The permission you want/need
SCOPES = moreData["permission-scope"]
# Path to the downloaded secret credentials file (the one you downloaded online)
CLIENT_SECRET_FILE = os.path.join(DIRECTORY_FOR_GMAIL_API,"client_secret.json")
# Name of the service (the one you created online)
APPLICATION_NAME = moreData["application-name"]


# scraper methods:

def extract_important_inforamtion(table_data):
    """Clean the list strings.

    Remove the not important characters, spacwes, newlines, ecetera.

    Args:
    table_data: list of html extracted table

    Returns:
        List with only the important data.
    """

    # for every row
    for a in range(len(table_data)):
            del table_data[a][0] # remove the first column (class id)
            for b in range(len(table_data[a])):
                new_text = table_data[a][b]
                # remove newlines and more
                new_text = "".join(new_text.split("-\n"))
                new_text = "".join(new_text.split("\n"))
                new_text = "".join(new_text.split("\r"))
                # remove spaces (https://stackoverflow.com/a/21484372/7827128)
                new_text = re.sub(r"^\s*(-\s*)?|(\s*-)?\s*$", "", new_text)
                # special thing (German: "H. to Hour")
                new_text = "Stunde".join(new_text.split("Std."))
                table_data[a][b] = new_text

                if b > 2:
                    if not table_data[a][3]:
                        table_data[a][b] = ""

    return table_data

def createHtmlMessage(table_data, class_url):
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

    # convert Json list to a custom and clean html table
    for a in range(1, len(table_data)):
        html_message += html_data["tr-start"]
        if not table_data[a][3]:
            for b in range(len(table_data[a])):
                html_message += html_data["td-start"] + html_data["strike-start"]
                if b < 3:
                    html_message += table_data[a][b]
                else:
                    html_message += "---"
                html_message += html_data["strike-end"] + html_data["td-end"]
        else:
            for b in range(len(table_data[a])):
                html_message += html_data["td-start"]
                html_message += table_data[a][b]
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
    html_message.encode('ascii','xmlcharrefreplace')

    return html_message

def compareLists(old_list, new_list):
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
    if (old_list is None):
        message_old_list = str(old_list)
    else:
        message_old_list = ''.join(map(str,old_list))
    logging.debug("old list: " + message_old_list)
    if (new_list is None):
        message_new_list = str(new_list)
    else:
        message_new_list = ''.join(map(str,new_list))
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
        return True # at this point we know, that the new table isn't empty

    # check if one list is bigger than the other
    if len(old_list) != len(new_list):
        # not "not is" but "!=" is used because it doesn't work after 256:
        # https://stackoverflow.com/questions/2239737/is-it-better-to-use-is-or-for-number-comparison-in-python
        print("len(old_list) " + str(len(old_list)) + " is not len(new_list) " + str(len(new_list)))
        logging.info("Change because of: old list (" + str(len(old_list)) + ") and new list (" + str(len(new_list)) + ") have different lengths")
        return True

    # if they are the same size iterate over them to find a difference
    for a in range(1, len(new_list)):
        for b in range(len(new_list[a])):
            if new_list[a][b] is not old_list[a][b]:
                print("new_list[a][b]:" + new_list[a][b] + " and old_list[a][b]: " + old_list[a][b])
                logging.info("Change because of: at [" + str(a) + "][" + str(b) +"] old list is \"" + old_list[a][b] + "\" and new list is \"" + new_list[a][b] + "\"")
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
            table = soup.find_all('table')[1]
            # remove tags and create list(https://stackoverflow.com/a/18544794/7827128)
            table_data = [[cell.text for cell in row("td")] for row in table ("tr")]
            print("Extracted table from " + x["url"] + ":")
            print(table_data)
            # extract the important information from the list
            table_data = extract_important_inforamtion(table_data)
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


        # if there is no old file, a new one, that is different to the old one continue
        if compareLists(old_json_table, new_json_table):

            subject = moreData["title-subject"] + x["name"]

            message_text = createHtmlMessage(table_data, x["url"])

            message_text = re.sub(r'[^\x00-\x7F]+',' ', message_text)

            print("Message:")
            print(message_text.encode('ascii', 'xmlcharrefreplace').decode('ascii'))
            print("send to")

            # 1. save new table as json file
            with open(DIRECTORY_FOR_TABLES + "/" + x["name"] + ".json", 'w') as file:
                json.dump(table_data, file)
                logging.debug("the file " + DIRECTORY_FOR_TABLES + "/" + x["name"] + ".json was successfully overwritten with the new list")

            # 2. send it to all recipients an email with the change
            for y in x["recipients"]:

                # create message
                message = CreateMessage(moreData["email"], y, subject, message_text)
                # create service (https://developers.google.com/gmail/api/quickstart/python)

                credentials = get_credentials()
                http = credentials.authorize(httplib2.Http())
                service = discovery.build('gmail', 'v1', http=http)
                # send the message
                if SendMessage(service, "me", message) is not None:
                    print("- succsessfully send to " + y)
                    logging.info("email was successfully send to " + y)
                else:
                    print("WARNING - Message could not be send to " + y)
                    logging.warning("email was not send to " + y)
        else:
            print("no changes to the class " + x["name"])
