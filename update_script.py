import os
import urllib.request

url = 'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/CoCoPreProcessorUI.py'
allowedWords = 'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/allowed_words.txt'
currentDirectory = os.getcwd()
urllib.request.urlretrieve(url, filename=currentDirectory + '/CoCoPreProcessorUI.py')
if not os.path.exists(currentDirectory + '/allowed_words.txt'):
    urllib.request.urlretrieve(allowedWords, filename=currentDirectory + '/allowed_words.txt')