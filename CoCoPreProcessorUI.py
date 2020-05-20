import sys
from functions import *
from functools import partial
from global_vars import tk
from tkinter import filedialog, Listbox, Label, Scrollbar, Frame, Entry, Button, Checkbutton
from lxml import html

    #####################
    #     OPEN FILE     #
    #####################


if len(sys.argv) < 2:
    tk.filename = filedialog.askopenfilename(initialdir=r"C:\Users\blank\Desktop\XML", title="Select file",
                                             filetypes=(("HTML files", "*.htm"), ("all files", "*.*")))
else:
    tk.filename = sys.argv[1]

# open the file as string, to replace tag-based substrings
# much easier to do before parsing html
with open(tk.filename, 'r', encoding='UTF-8') as fi, \
        open('tmp.htm', 'w', encoding='UTF-8') as fo:
    new_str = fi.read()
    new = new_str.replace('CO2', 'CO<sub>2</sub>')  # replaces every occurrence of CO2
    new = new.replace('\u2013', '-')  # replaces en dash with normal dash
    new = new.replace('\xa0', ' ')  # replaces non breaking spaces
    # REMOVE WRONG LINE BREAK HERE BECAUSE I CANT FIGURE OUT HOW TO DO IT WITHIN THE PARSER
    new = re.sub(r"(?sm)(?<=[a-zöüä\,;\xa0])\s*?</p>\s*?<p>(?=[a-zöäü][^)])", ' ', new)
    fo.write(new)
    fo.close()

    ################
    # PARSING FILE #
    ################


def generate_file(tree, entryCkb):
    if fRemoveEmptyRows.get():
        remove_empty_rows(tree)
    if fMergeTablesVertically.get():
        merge_tables_vertically(tree)
    if fSetUnorderedList.get():
        set_unordered_list(tree)
    if fFootnotetables.get():
        set_footnote_tables(tree)
    if fReplaceNumbers.get():
        replace_number_list(tree, listboxNumbers)
    if fReplaceWords.get():
        replace_word_list(tree, listboxWords)
    # if fSplitRowSpan.get():
    #     split_rowspan()
    if fSpanHeaders.get():
        set_span_headers(tree, leSpanHeaders)
    if fSetHeaders.get():
        set_headers(tree)
    if fIsFondsReport.get():
        if fFixTsdSeparators.get():
            fix_tsd_separators(tree, ',')
        if fBreakFondsTable.get():
            break_fonds_table(tree)
    if fRenamePictures.get():
        rename_pictures(tree)
    # wrap all table contents in p-tags
    # wrap(tree, "p")
    # write to new file in source folder
    tree.write(os.path.splitext(tk.filename)[0] + '_modified.htm', encoding='UTF-8', method='html')
    if fSupElements.get():
        sup_elements(os.path.splitext(tk.filename)[0] + '_modified.htm', entryCkb)
    tk.destroy()

with open('tmp.htm', 'r+', encoding="utf-8") as input_file:
    tree = html.parse(input_file)
    tree = parse_and_clean(tree)
    ############
    # BUILD UI #
    ############

    # MASTER WINDOW
    tk.title('CoCo PreProcessor UI')
    frameTop = Frame(tk, height=3)
    frameTop.pack(side='top', fill='x')
    masterLabel = Label(frameTop,
                        text='Double Click on list entry to copy to clipboard\n'
                             'Single Click to fix in yellow entry box. ENTER to confirm changes!',
                        width=55, font=('Arial', 10, 'bold'))
    masterLabel.pack(side='left')

    # FRAME 1
    frameNumbers = Frame(tk, width=25, height=50)
    frameLbNumbers = Frame(frameNumbers, width=45, height=48)
    frameLbNumbers.pack(side='bottom')
    frameNumbers.pack(fill='y', side='left')
    # LISTBOX 1
    listboxNumbers = Listbox(frameLbNumbers, width=20, height=48)
    listboxNumbers.pack(side='left', expand=True)
    listboxNumbers.bind('<Double-Button-1>', listbox_copy)

    # SCROLLBAR 1
    scrollbarNumbers = Scrollbar(frameLbNumbers, orient="vertical")
    scrollbarNumbers.config(command=listboxNumbers.yview)
    scrollbarNumbers.pack(side="left", fill="y")
    # CONFIG 1
    listboxNumbers.config(yscrollcommand=scrollbarNumbers.set)
    get_false_Numbers(tree, lFalseNumberMatches)
    for e in range(len(lFalseNumberMatches)):
        listboxNumbers.insert(e, lFalseNumberMatches[e])
    # ENTRY BOX NUMBERS
    # use entry widget to display/edit selection
    entryNumbers = Entry(frameNumbers, width=25, bg='yellow')

    entryNumbers.pack(side='top')
    entryNumbers.bind('<Return>', partial(set_list, listboxNumbers, entryNumbers))
    listboxNumbers.bind('<ButtonRelease-1>', partial(get_list, listboxNumbers, entryNumbers))
    entryNumbers.focus_force()

    # FRAME 2
    frameWords = Frame(tk, width=50, height=50)
    frameLbWords = Frame(frameWords, width=45, height=48)
    frameLbWords.pack(side='bottom')
    frameWords.pack(fill='y', side='left')
    # LISTBOX 2
    listboxWords = Listbox(frameLbWords, width=45, height=48)
    listboxWords.pack(side='left', expand=True)
    listboxWords.bind('<Double-Button-1>', listbox_copy)
    # SCROLLBAR 2
    scrollbarWords = Scrollbar(frameLbWords, orient="vertical")
    scrollbarWords.config(command=listboxWords.yview)
    scrollbarWords.pack(side="left", fill="y")
    # CONFIG 2
    listboxWords.config(yscrollcommand=scrollbarWords.set)
    lAllFalseWordMatches = get_false_Words(tree)
    for e in range(len(lAllFalseWordMatches)):
        listboxWords.insert(e, lAllFalseWordMatches[e])

    # ENTRY BOX WORDS
    # use entry widget to display/edit selection
    entryWords = Entry(frameWords, width=50, bg='yellow')
    entryWords.insert(0, 'Click on an item in the listbox')
    entryWords.pack(side='top')
    entryWords.bind('<Return>', partial(set_list, listboxWords, entryWords))
    listboxWords.bind('<ButtonRelease-1>', partial(get_list, listboxWords, entryWords))
    entryWords.focus_force()
    # buttonWords = Button(frameWords, text='REPLACE AND QUIT', command=replace_list)
    # buttonWords.pack(side='top')

    # FRAME 3
    frameChecks = Frame(tk, width=25, height=50)
    frameChecks.pack(fill='y', side='left')
    ckbHeaders = Checkbutton(frameChecks, anchor='w', text='convert headers', variable=fSetHeaders)
    ckbFootnotes = Checkbutton(frameChecks, anchor='w', text='convert footnotes', variable=fFootnotetables)
    ckbEmptyRows = Checkbutton(frameChecks, anchor='w', text='remove empty rows', variable=fRemoveEmptyRows)
    ckbWords = Checkbutton(frameChecks, anchor='w', text='replace fixed words', variable=fReplaceWords)
    ckbNumbers = Checkbutton(frameChecks, anchor='w', text='replace fixed numbers', variable=fReplaceNumbers)
    ckbVertMerge = Checkbutton(frameChecks, anchor='w', text='vertically merge tables (§§)',
                               variable=fMergeTablesVertically)
    ckbSpanHeaders = Checkbutton(frameChecks, anchor='w', text='analyze heading (BETA)', variable=fSpanHeaders)
    ckbRenamePics = Checkbutton(frameChecks, anchor='w', text='rename .png to .jpg', variable=fRenamePictures)

    ckbHeaders.pack(side='top', anchor='w')
    ckbFootnotes.pack(side='top', anchor='w')
    ckbEmptyRows.pack(side='top', anchor='w')
    ckbWords.pack(side='top', anchor='w')
    ckbNumbers.pack(side='top', anchor='w')
    ckbVertMerge.pack(side='top', anchor='w')
    ckbSpanHeaders.pack(side='top', anchor='w')
    ckbRenamePics.pack(side='top', anchor='w')

    # Sup check button
    labelCkb = Label(frameChecks, text='\nSuperscript elements')
    labelCkb.pack(side='top', anchor='w')
    frameCkb = Frame(frameChecks, width=25, height=5)
    frameCkb.pack(side='top')
    ckbSup = Checkbutton(frameCkb, anchor='w', variable=fSupElements)
    ckbSup.pack(side='left', anchor='w')
    entryCkb = Entry(frameCkb, width=23, )
    entryCkb.insert(0, ', '.join(lSupElements))
    entryCkb.pack(side='left')

    if fIsFondsReport.get():
        ckbTsdFix = Checkbutton(frameChecks, anchor='w', text='fix tsd separators', variable=fFixTsdSeparators)
        ckbBreakFondsTable = Checkbutton(frameChecks, anchor='w', text='break Vermögensaufstellung', variable=fBreakFondsTable)
        ckbTsdFix.pack(side='top', anchor='w')
        ckbBreakFondsTable.pack(side='top', anchor='w')

    buttonGenerate = Button(frameChecks, height=3, width=20, bd=2, fg='white', font=('Arial', 15),
                            text='GENERATE FILE \n AND QUIT', command=partial(generate_file, tree, entryCkb), bg='dark green')
    buttonGenerate.pack(side='bottom')
    tk.mainloop()

os.remove('tmp.htm')  # remove original
if bFoundError:
    input('Fix displayed errors and press ENTER to quit!')
