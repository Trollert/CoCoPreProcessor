import os
from urllib.request import urlretrieve, urlopen
from urllib.parse import urlparse
import configparser

url = ['https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/CoCoPreProcessorUI.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/allowed_words.txt',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/functions.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/global_vars.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/patterns.py',
       'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/tk_functions.py']
currentDirectory = os.getcwd()
for file in url:
    basename = os.path.basename(urlparse(file).path)
    urlretrieve(file, filename=currentDirectory + '/' + basename)

if not os.path.exists(currentDirectory + '/user_words.txt'):
    open(currentDirectory + '/user_words.txt', 'a').close()

Config = configparser.ConfigParser()
if os.path.exists(os.getcwd() + '/preproc_config.ini'):
    Config.read('preproc_config.ini')
    Config['VERSION']['pre_proc_version'] = urlopen('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/_version_.txt').read().decode('utf-8')
    with open(os.getcwd() + '/preproc_config.ini', 'w') as configfile:
        Config.write(configfile)