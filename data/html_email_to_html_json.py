'''
With this script you can convert an html email in the file email.html in the same directory
to an JSON file which is also editable and nice to read for the main script.py
'''

import json

# load all the lines from the html email
with open("email.html") as file:
    content = file.readlines()

# create empty walking string
walking_string = ""
# create empty dictionary
json_list = {}

# walk through all lines of the html email
for x in content:
    # delete all the not important things like newlines, tabs, etc. from each string
    x = x.strip()
    # check if this is not an empty line
    if x is not "":
        # if this is found in the comments - add a new entry to the dictionary
        if x.find("top-title-begin") != -1:
            json_list['head'] = walking_string
            walking_string = ""
            # etc.
        elif x.find("top-title-end") != -1:
            json_list['title-body'] = walking_string
            walking_string = ""
        elif x.find("table-placeholder-begin") != -1:
            json_list['top'] = walking_string
            walking_string = ""
        elif x.find("tr-nice-tag-open-begin") != -1:
            walking_string = ""
        elif x.find("tr-nice-tag-open-end") != -1:
            json_list['tr-start'] = walking_string
            walking_string = ""
        elif x.find("td-nice-tag-open-begin") != -1:
            walking_string = ""
        elif x.find("td-nice-tag-open-end") != -1:
            json_list['td-start'] = walking_string
            walking_string = ""
        elif x.find("td-nice-tag-close-begin") != -1:
            walking_string = ""
        elif x.find("td-nice-tag-close-end") != -1:
            json_list['td-end'] = walking_string
            walking_string = ""
        elif x.find("tr-nice-tag-close-begin") != -1:
            walking_string = ""
        elif x.find("tr-nice-tag-close-end") != -1:
            json_list['tr-end'] = walking_string
            walking_string = ""
        elif x.find("strike-tag-open-begin") != -1:
            walking_string = ""
        elif x.find("strike-tag-open-end") != -1:
            json_list['strike-start'] = walking_string
            walking_string = ""
        elif x.find("strike-tag-close-begin") != -1:
            walking_string = ""
        elif x.find("strike-tag-close-end") != -1:
            json_list['strike-end'] = walking_string
            walking_string = ""
        elif x.find("table-placeholder-end") != -1:
            walking_string = ""
        elif x.find("link-plan-placeholder-begin") != -1:
            walking_string += "<a href=\""
            json_list['middle'] = walking_string
            walking_string = ""
        elif x.find("link-plan-placeholder-end") != -1:
            walking_string = ""
        elif x.find("linktext-plan-placeholder-begin") != -1:
            walking_string = "\">" + walking_string
            json_list['space-between-link-and-text'] = walking_string
            walking_string = ""
        elif x.find("linktext-plan-placeholder-end") != -1:
            json_list['linktext-plan'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-01-placeholder-begin") != -1:
            json_list['bottom'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-01-placeholder-end") != -1:
            json_list['bottom-text-01'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-02-placeholder-begin") != -1:
            json_list['bottom-text-space-01'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-02-placeholder-end") != -1:
            json_list['bottom-text-02'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-03-placeholder-begin") != -1:
            json_list['bottom-text-space-02'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-03-placeholder-end") != -1:
            json_list['bottom-text-03'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-04-placeholder-begin") != -1:
            json_list['bottom-text-space-03'] = walking_string
            walking_string = ""
        elif x.find("bottom-text-04-placeholder-end") != -1:
            json_list['bottom-text-04'] = walking_string
            walking_string = ""
        else:
            walking_string += x
# add the rest of the content to "html-end"
json_list['end'] = walking_string

# convert the dictionary to a JSON file
with open('html.json', 'w') as outfile:
    # through indent=2 each entry will be on a new line
    # source: https://stackoverflow.com/a/17055135/7827128
    json.dump(json_list, outfile, indent=2, ensure_ascii=False)
