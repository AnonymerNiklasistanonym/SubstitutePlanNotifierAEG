# can be used to convert your website to a simple string - just put it in a text file with the name "data.txt" and run

import json

# read input file and remove all not important characters
with open("data.txt", "r") as input_file:
    data = input_file.read().replace('\n', '').replace('\t', '').replace('\r', '')

# output the cleaned data to json file
with open("data.json", "w") as output_file:
    json.dump(data, output_file)
