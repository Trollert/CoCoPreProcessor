import sys
import re
import os
from functools import partial
from tkinter import filedialog, Listbox, Label, Scrollbar, Frame, Entry, Button, Checkbutton
from lxml import html
from urllib.request import urlopen, urlretrieve
import configparser

# custom imports
from functions import replace_word_list, replace_number_list, set_footnote_tables, get_false_Words, get_false_Numbers, set_headers, set_unordered_list, remove_empty_rows, merge_tables_vertically,sup_elements, set_span_headers, rename_pictures, fix_tsd_separators, break_fonds_table, wrap, first_cleanse
from tk_functions import FancyListbox, listbox_copy, set_list, get_list
from patterns import lSupElements
import global_vars

# read config file, create if not found
Config = configparser.ConfigParser()
global_vars.working_folder = os.getcwd()
if os.path.exists(global_vars.working_folder + '/preproc_config.ini'):
    Config.read('preproc_config.ini')
    global_vars.opening_folder = Config['PATHS']['opening_dir']
    _version_ = Config['VERSION']['pre_proc_version']
    _current_version_ = urlopen('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/_version_.txt').read().decode('utf-8')
    if _version_ != _current_version_:
        global_vars.bUpToDate = False
else:
    print('No config file found, update script with update_script.py and restart'
          ' CoCoPreProcessorUI.py before proceeding! This message will still appear though, so dont get confused')
    urlretrieve('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py', filename=global_vars.working_folder + '/update_script.py')
    Config['PATHS'] = {}
    Config['PATHS']['opening_dir'] = filedialog.askdirectory(title='Choose the directory to open when using CoCo-PreProcessor!')
    workingFolder = Config['PATHS']['opening_dir']
    Config['VERSION'] = {}
    Config['VERSION']['pre_proc_version'] = urlopen('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/_version_.txt').read().decode('utf-8')
    with open(global_vars.working_folder + '/preproc_config.ini', 'w') as configfile:
        Config.write(configfile)

from tk_functions import listbox_copy, set_list, get_list

#####################
#     OPEN FILE     #
#####################
if len(sys.argv) < 2:
    global_vars.tk.filename = filedialog.askopenfilename(initialdir=global_vars.opening_folder, title="Select file",
                                                         filetypes=(("HTML files", "*.htm"), ("all files", "*.*")))
    global_vars.report_path = os.path.dirname(global_vars.tk.filename)
else:
    global_vars.tk.filename = sys.argv[1]

# open the file as string, to replace tag-based substrings
# much easier to do before parsing html
with open(global_vars.tk.filename, 'r', encoding='UTF-8') as fi, \
        open('tmp.htm', 'w', encoding='UTF-8') as fo:
    new_str = fi.read()
    new = new_str.replace('CO2', 'CO<sub>2</sub>')  # replaces every occurrence of CO2

    new = new.replace('—', '-')  # replaces en dash with normal dash
    new = new.replace('\u2013', '-')  # replaces en dash with normal dash
    new = new.replace('&nbsp;', ' ')  # replaces non breaking spaces
    # REMOVE WRONG LINE BREAK HERE BECAUSE I CANT FIGURE OUT HOW TO DO IT WITHIN THE PARSER
    new = re.sub(r"(?sm)(?<=[a-zöüä\,;\xa0])\s*?</p>\s*?<p>(?=[a-zöäü][^)])", ' ', new)
    fo.write(new)
    fo.close()

    ################
    # PARSING FILE #
    ################


def generate_file(tree, entryCkb):
    if global_vars.fRemoveEmptyRows.get():
        remove_empty_rows(tree)
    if global_vars.fMergeTablesVertically.get():
        merge_tables_vertically(tree)
    if global_vars.fReplaceNumbers.get():
        replace_number_list(tree, listboxNumbers, global_vars.report_path)
    if global_vars.fReplaceWords.get():
        replace_word_list(tree, listboxWords, global_vars.report_path)
    if global_vars.fSetUnorderedList.get():
        set_unordered_list(tree)
    if global_vars.fFootnotetables.get():
        set_footnote_tables(tree)
    # if fSplitRowSpan.get():
    #     split_rowspan()
    if global_vars.fSpanHeaders.get():
        set_span_headers(global_vars.leSpanHeaders)
    if global_vars.fSetHeaders.get():
        set_headers(tree)
    if global_vars.fIsFondsReport.get():
        if global_vars.fFixTsdSeparators.get():
            fix_tsd_separators(tree, ',')
        if global_vars.fBreakFondsTable.get():
            break_fonds_table(tree)
    if global_vars.fRenamePictures.get():
        rename_pictures(tree)
    # wrap all table contents in p-tags
    # wrap(tree, "p")
    # write to new file in source folder
    tree.write(os.path.splitext(global_vars.tk.filename)[0] + '_modified.htm', encoding='UTF-8', method='html')
    if global_vars.fSupElements.get():
        sup_elements(os.path.splitext(global_vars.tk.filename)[0] + '_modified.htm', entryCkb)
    # clean up user_words.txt
    f = open(global_vars.working_folder + '/user_words.txt', 'r', encoding='utf-8')
    l = f.read().splitlines()
    f.close()
    f = open(global_vars.working_folder + '/user_words.txt', 'w', encoding='utf-8')

    f.write('\n'.join(list(dict.fromkeys(l))) + '\n')
    f.close()

    global_vars.tk.destroy()


with open('tmp.htm', 'r+', encoding="utf-8") as input_file:
    tree = html.parse(input_file)
    tree = first_cleanse(tree)
    ############
    # BUILD UI #
    ############

    # MASTER WINDOW
    global_vars.tk.title('CoCo PreProcessor UI')
    frameTop = Frame(global_vars.tk, height=3)
    frameTop.pack(side='top', fill='x')
    masterLabel = Label(frameTop,
                        text='Double Click on list entry to copy to clipboard\n'
                             'Single Click to fix in yellow entry box. ENTER to confirm changes!',
                        width=55, font=('Arial', 10, 'bold'))
    masterLabel.pack(side='left')
    if not global_vars.bUpToDate:
        versionLabel = Label(frameTop,
                        text='New Version available!\n'
                             'Please update with update_script!',
                        width=30, font=('Arial', 9, 'bold'), fg='red')
        versionLabel.pack(side='right')


    # FRAME 1
    frameNumbers = Frame(global_vars.tk, width=25, height=50)
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
    get_false_Numbers(tree, global_vars.report_path)
    for e in range(len(global_vars.lFalseNumberMatches)):
        listboxNumbers.insert(e, global_vars.lFalseNumberMatches[e])
    # ENTRY BOX NUMBERS
    # use entry widget to display/edit selection
    entryNumbers = Entry(frameNumbers, width=25, bg='yellow')

    entryNumbers.pack(side='top')
    entryNumbers.bind('<Return>', partial(set_list, listboxNumbers, entryNumbers))
    listboxNumbers.bind('<ButtonRelease-1>', partial(get_list, listboxNumbers, entryNumbers))
    entryNumbers.focus_force()

    # FRAME 2
    frameWords = Frame(global_vars.tk, width=50, height=50)
    frameLbWords = Frame(frameWords, width=45, height=48)
    frameLbWords.pack(side='bottom')
    frameWords.pack(fill='y', side='left')
    # LISTBOX 2
    listboxWords = FancyListbox(frameLbWords, width=45, height=48)
    listboxWords.pack(side='left', expand=True)
    listboxWords.bind('<Double-Button-1>', listbox_copy)
    # SCROLLBAR 2
    scrollbarWords = Scrollbar(frameLbWords, orient="vertical")
    scrollbarWords.config(command=listboxWords.yview)
    scrollbarWords.pack(side="left", fill="y")
    # CONFIG 2
    listboxWords.config(yscrollcommand=scrollbarWords.set)
    get_false_Words(tree, global_vars.report_path)
    for e in range(len(global_vars.lAllFalseWordMatches)):
        listboxWords.insert(e, global_vars.lAllFalseWordMatches[e])

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
    frameChecks = Frame(global_vars.tk, width=25, height=50)
    frameChecks.pack(fill='y', side='left')
    ckbHeaders = Checkbutton(frameChecks, anchor='w', text='convert headers', variable=global_vars.fSetHeaders)
    ckbFootnotes = Checkbutton(frameChecks, anchor='w', text='convert footnotes', variable=global_vars.fFootnotetables)
    ckbEmptyRows = Checkbutton(frameChecks, anchor='w', text='remove empty rows', variable=global_vars.fRemoveEmptyRows)
    ckbWords = Checkbutton(frameChecks, anchor='w', text='replace fixed words', variable=global_vars.fReplaceWords)
    ckbNumbers = Checkbutton(frameChecks, anchor='w', text='replace fixed numbers', variable=global_vars.fReplaceNumbers)
    ckbVertMerge = Checkbutton(frameChecks, anchor='w', text='vertically merge tables (§§)',
                               variable=global_vars.fMergeTablesVertically)
    ckbSpanHeaders = Checkbutton(frameChecks, anchor='w', text='analyze heading (BETA)', variable=global_vars.fSpanHeaders)
    ckbRenamePics = Checkbutton(frameChecks, anchor='w', text='rename .png to .jpg', variable=global_vars.fRenamePictures)

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
    ckbSup = Checkbutton(frameCkb, anchor='w', variable=global_vars.fSupElements)
    ckbSup.pack(side='left', anchor='w')
    entryCkb = Entry(frameCkb, width=23, )
    entryCkb.insert(0, ', '.join(lSupElements))
    entryCkb.pack(side='left')

    if global_vars.fIsFondsReport.get():
        ckbTsdFix = Checkbutton(frameChecks, anchor='w', text='fix tsd separators', variable=global_vars.fFixTsdSeparators)
        ckbBreakFondsTable = Checkbutton(frameChecks, anchor='w', text='break Vermögensaufstellung',
                                         variable=global_vars.fBreakFondsTable)
        ckbTsdFix.pack(side='top', anchor='w')
        ckbBreakFondsTable.pack(side='top', anchor='w')

    buttonGenerate = Button(frameChecks, height=3, width=20, bd=2, fg='white', font=('Arial', 15),
                            text='GENERATE FILE \n AND QUIT', command=partial(generate_file, tree, entryCkb),
                            bg='dark green')
    buttonGenerate.pack(side='bottom')
    global_vars.tk.mainloop()

os.remove('tmp.htm')  # remove original
if global_vars.bFoundError.get():
    input('Fix displayed errors and press ENTER to quit!')
