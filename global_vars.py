from tkinter import Tk, BooleanVar

# global tree object
tree = None

# global lists
lAllFalseWordMatches = []
lFalseNumberMatches = []
leSpanHeaders = []

# current working directory
report_path = ''
opening_folder = ''
working_folder = ''


# global tkinter vars
tk = Tk()
fIsFondsReport = BooleanVar(value=0)

# Bools to define which functions to call
bSplitRowspan = BooleanVar(value=1)
bReplaceWords = BooleanVar(value=1)
bReplaceNumbers = BooleanVar(value=1)
bFootnotetables = BooleanVar(value=1)
bFixNumbers = BooleanVar(value=1)
bRenamePictures = BooleanVar(value=1)
bMergeTablesVertically = BooleanVar(value=1)
bSpanHeaders = BooleanVar(value=0)
bSetUnorderedList = BooleanVar(value=1)
bSetHeaders = BooleanVar(value=1)
bSupElements = BooleanVar(value=0)
bRemoveEmptyRows = BooleanVar(value=1)
bFixTsdSeparators = BooleanVar(value=1)
bBreakFondsTable = BooleanVar(value=1)

# global flags
bFoundError = False
lsErrorLog = []
bUpToDate = True
