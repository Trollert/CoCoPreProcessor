import re

##################
# REGEX PATTERNS #
##################

# compile footnote patterns as regex object
regFootnote = [
    re.compile(r'\s*?[(\[]?\d{1,2}[)\]]?\s*?'),        # 1; 1); 1]; (1); [1]
    re.compile(r'\s*?\(?\*{1,9}\)?\s*?'),              # *; *******); (****)
    re.compile(r'\s*?[a-z]\)?\s*?')                    # a; a)
    ]

# compile number format as regex objects
regNumbers = [
    re.compile(r'(^\s*?(§§)?\(?\s*?[-+T$£]{0,3}\s*?\d{1,3}\s*?[€$%£T]{0,2}\s*?\)?$)', re.MULTILINE),
    # 123 has to be first, to prevent double matches
    re.compile(r'(^\s*?(§§)?\(?\s*?[-+T€£]{0,3}\s*?\d{1,3}(\.\d{3})*?(,\d{1,5})?\s*?[€%‰£]?\s*?\)?\s*?(p\.a\.)?\s*?$)', re.MULTILINE),
    # 123.123,12000 ; 123,1 ; 123
    re.compile(r'(^\s*?(§§)?\(?\s*?[-+T$£]{0,3}\s*?\d{1,3}(,\d{3})*?(\.\d{1,5})?\s*?[$%‰£]?\s*?\)?\s*?(p\.a\.)?\s*?$)', re.MULTILINE),
    # 123,123.12 ; 123.1 ; 123
    re.compile(r'(^\s*?(§§)?\(?\s*?[-+T€£]{0,3}\s*?\d{1,3}(\s\d{3})*?(,\d{1,5})?\s*?[€%‰£]?\s*?\)?\s*?(p\.a\.)?\s*?$)', re.MULTILINE),
    # 123 123,12 ; 123,1 ; 123
    re.compile(r'(^\s*?(§§)?\(?\s*?[-+T$£]{0,3}\s*?\d{1,3}(\s\d{3})*?(\.\d{1,5})?\s*?[$€%‰£]?\s*?\)?\s*?(p\.a\.)?\s*?$)', re.MULTILINE)
    # 123 123.12 ; 123.1 ; 123
    ]

# compile miscellaneous table content
regMisc = [
    re.compile(r'^\s*?(§§)?(n\/a|n\.a\.?|n\/m)\s*?$', re.IGNORECASE),         # n/a; n/m; n.a; n.a.
    re.compile(r'^[-.,§\s*]+$', re.MULTILINE),                                 # empty cells and placeholder -,. §
    re.compile(r'^.*[A-Za-z]{2,}.*$', re.DOTALL)                              # text
    # re.compile('^\s*?(§§)?(19|20)\d{2}\s*?$', re.MULTILINE),  # year 1900 - 2099
    # re.compile('^\s*?(§§)?\(?[0123]?\d?[./-]?[0123]?\d[./-](19|20)?\d{2}\)?\s*?$', re.MULTILINE),
    ]

# compile possible header content
regHeaderContent = [
    re.compile(r'^\s*?(§§)?\(?(in)?\s*?(Tsd|Mio|Mrd|T|Millionen|Million|billion|Milliarden|tausend)?\.?\s?([€$£%‰]|EUR|TEUR|Jahre|tagen|prozent|qm|m2|sqm|m|km)\)?\s?(Tsd|Mio|Mrd|T|Millionen|Million|billion|Milliarden|tausend|thousands)?\s*?$',
               re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*?(§§)?\(?(\$|€|£)(’|‘|\')(000|m)\)?\s*?$', re.IGNORECASE | re.MULTILINE)
]

regUnorderedList = [
    re.compile(r'^\s*?[\\\\►•·■\-□^→/]{1,2}\s?', re.MULTILINE)
]

regFalseWords = [
    re.compile(r'(\b[A-ZÖÄÜa-zäöüß][a-zäöüß]*?[a-zäöüß][A-ZÄÖÜ][a-zäöüß]*?\b)', re.MULTILINE),  # CashFlow, cashFlow
    re.compile(r'(\b[A-ZÖÄÜa-zäöüß][a-zäöüß]*?\b-\b[a-zäöüß]{1,}?\b)', re.MULTILINE),  # ex-terne, Ex-terne
    re.compile(r'\b[A-ZÖÄÜa-zäöüß]{1,}?soder\b', re.MULTILINE),  # Unternehmungsoder
    re.compile(r'\b[A-ZÖÄÜa-zäöüß]{1,}?sund\b', re.MULTILINE)  # Unternehmungsund
]

reg_false_break_indicator_end = re.compile(r'[a-zäöüß,]\s?$')

reg_false_break_indicator_start = re.compile(r'^\s?[a-zäöü]')

# get list of allowed text elements
lAllowedWords = open('allowed_words.txt', encoding='UTF-8').read().splitlines() + open('user_words.txt', encoding='UTF-8').read().splitlines()
# get list of sup-always elements
lSupElements = [
    '©',
    '®',
    '™'
]
