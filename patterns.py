import re

##################
# REGEX PATTERNS #
##################

# compile footnote patterns as regex object
regFootnote = [
    re.compile('\s*\d{1,2}\s*'),
    re.compile('\s*\(?\*{1,9}\)?\s*'),
    re.compile('\s*[a-z]\s*'),
    re.compile('\s*\d{1,2}\)\s*'),
    re.compile('\s*[(\[]\d{1,2}[)\]]\s*')
]

# compile number format as regex objects
regNumbers = [
    re.compile('(^\s*?(§§)?\(?\s*?[-+$£]{0,3}\s*?\d{1,3}[ €$%£]{0,2}\s*?\)?$)', re.MULTILINE),
    # 123 has to be first, to prevent double matches
    re.compile('(^\s*?(§§)?\(?\s*?[-+€£]{0,3}\s*?\d{1,3}(\.\d{3})*?(,\d{1,5})?\s*?[€%‰£]?\s*?\)?\s*?$)', re.MULTILINE),
    # 123.123,12000 ; 123,1 ; 123
    re.compile('(^\s*?(§§)?\(?\s*?[-+$£]{0,3}\s*?\d{1,3}(,\d{3})*?(\.\d{1,5})?\s*?[$%‰£]?\s*?\)?\s*?$)', re.MULTILINE),
    # 123,123.12 ; 123.1 ; 123
    re.compile('(^\s*?(§§)?\(?\s*?[-+€£]{0,3}\s*?\d{1,3}(\s\d{3})*?(,\d{1,5})?\s*?[€%‰£]?\s*?\)?\s*?$)', re.MULTILINE),
    # 123 123,12 ; 123,1 ; 123
    re.compile('(^\s*?(§§)?\(?\s*?[-+$£]{0,3}\s*?\d{1,3}(\s\d{3})*?(\.\d{1,5})?\s*?[€%‰£]?\s*?\)?\s*?$)', re.MULTILINE),
    # 123 123.12 ; 123.1 ; 123
    re.compile('^\s*?(§§)?(%|n\/a|n\.a|n\/m)\s*?$', re.IGNORECASE),

    # other allowed cell content
    re.compile('^[-.,§\s]+$', re.MULTILINE),  # empty cells and placeholder -,.
    re.compile('^\s*?(§§)?(19|20)\d{2}\s*?$', re.MULTILINE),  # year 1900 - 2099
    re.compile('^\s*?(§§)?\(?[0123]?\d?[./-]?[0123]?\d[./-](19|20)?\d{2}\)?\s*?$', re.MULTILINE),
    # dates 12.02.1991; 12.31.91: 12.31.2091
    re.compile('^.*[A-Za-z]{2,}.*$', re.DOTALL),  # text
    re.compile('^\s*?(§§)?(in)?\s*?(TEUR|Tsd|Mio|Mrd|Jahre|T)?\.?\s?([€$£]|EUR)\s*?$', re.IGNORECASE | re.MULTILINE),
    # T€, Mio. €, Mrd. €, in
    re.compile('^\s*?(§§)?\(?(\$|€|£)(’|‘)(000|m)\)?\s*?$',
               re.IGNORECASE | re.MULTILINE)
]

regHeaderContent = [
    regNumbers[8],  # dates
    regNumbers[7],  # year
    regNumbers[10],  # T€, Mio. €, Mrd. €, in €
    re.compile('^\s*?(in)?\s*?(mio)?\.?(TEUR|TSD|MRD|EUR)?\s*?$', re.IGNORECASE | re.MULTILINE),  # T€, Mio. €, Mrd. €, in €
    re.compile('^\s*?[0123]?\d\.?\s*?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*?(19|20)?\d{2}\s*?$',
               re.IGNORECASE | re.MULTILINE),
    re.compile('^\s*?[0123]?\d\.?\s*?(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dec)\.?\s*?(19|20)?\d{2}\s*?$',
               re.IGNORECASE | re.MULTILINE),
    re.compile('^\s*?(in)?\s*?(Millionen|Milliarden|tausend)?\s*?(€|\$|£|euro|eur)\s*?$',
               re.IGNORECASE | re.MULTILINE),
    regNumbers[11]
]

regUnorderedList = [
    re.compile('^\s*?[\\►•·■\-□^→/]\s?', re.MULTILINE)
]

regFalseWords = [
    re.compile(r'(\b[A-ZÖÄÜa-zäöüß][a-zäöüß]*?[a-zäöüß][A-ZÄÖÜ][a-zäöüß]*?\b)', re.MULTILINE),  # CashFlow, cashFlow
    re.compile(r'(\b[A-ZÖÄÜa-zäöüß][a-zäöüß]*?\b-\b[a-zäöüß]{1,}?\b)', re.MULTILINE),  # ex-terne, Ex-terne
    re.compile(r'\b[A-ZÖÄÜa-zäöüß]{1,}?soder\b', re.MULTILINE),  # Unternehmungsoder
    re.compile(r'\b[A-ZÖÄÜa-zäöüß]{1,}?sund\b', re.MULTILINE)  # Unternehmungsund
]

# get list of allowed text elements
lAllowedWords = open('allowed_words.txt', encoding='UTF-8').read().splitlines() + open('user_words.txt', encoding='UTF-8').read().splitlines()
# get list of sup-always elements
lSupElements = [
    '©',
    '®',
    '™'
]
