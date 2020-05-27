from tkinter import Tk, BooleanVar

# global lists
lAllFalseWordMatches = []
lFalseNumberMatches = []
leSpanHeaders = []

# current working directory
current_path = ''

# global tkinter vars
tk = Tk()
fIsFondsReport = BooleanVar(value=0)

# Bools to define which functions to call

fReplaceWords = BooleanVar(value=1)
fReplaceNumbers = BooleanVar(value=1)
fFootnotetables = BooleanVar(value=1)
fFixNumbers = BooleanVar(value=1)
fRenamePictures = BooleanVar(value=1)
fMergeTablesVertically = BooleanVar(value=1)
fSpanHeaders = BooleanVar(value=0)
fSetUnorderedList = BooleanVar(value=1)
fSetHeaders = BooleanVar(value=1)
fSupElements = BooleanVar(value=0)
fRemoveEmptyRows = BooleanVar(value=1)
fFixTsdSeparators = BooleanVar(value=1)
fBreakFondsTable = BooleanVar(value=1)
# list of function calls
lfFunctCalls = []

# global flags
bFoundError = BooleanVar(value=0)
bUpToDate = True
