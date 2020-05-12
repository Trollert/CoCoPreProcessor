import os
import urllib.request

url = 'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/CoCoPreProcessorUI.py'
# allowedWords = 'https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/allowed_words.txt'
currentDirectory = os.getcwd()
urllib.request.urlretrieve(url, filename=currentDirectory + '/CoCoPreProcessorUIdownload.py')
# urllib.request.urlretrieve(allowedWords, filename=currentDirectory + '/allowed_wordsdownload.txt')