from tkinter import Tk, BooleanVar

# global lists
lAllFalseWordMatches = []
lFalseNumberMatches = []
leSpanHeaders = []

# global flags
bFoundError = False

# global tkinter vars
tk = Tk()
fIsFondsReport = BooleanVar(value=0)

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