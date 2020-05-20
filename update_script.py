import os
from urllib.request import urlretrieve
from urllib.parse import urlparse

url = ['https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/CoCoPreProcessorUI.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/allowed_words.txt',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/functions.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/global_vars.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/patterns.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py']
currentDirectory = os.getcwd()
for file in url:
    basename = os.path.basename(urlparse(file).path)
    urlretrieve(file, filename=currentDirectory + '/' + basename)
    # urlretrieve(allowedWords, filename=currentDirectory + '/allowed_words.txt')

if not os.path.exists(currentDirectory + '/user_words.txt'):
    open(currentDirectory + '/user_words.txt', 'a').close()