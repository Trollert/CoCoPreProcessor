import sys
import re
import os
from functools import partial
from tkinter import filedialog, Label, Frame, Entry, Button, Checkbutton
from lxml import html
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError
import configparser

# custom imports
from functions import big_fucking_table, replace_word_list, replace_number_list, set_footnote_tables, get_false_words, get_false_numbers, set_headers, set_unordered_list, remove_empty_rows, merge_tables_vertically, sup_elements, set_span_headers, rename_pictures, fix_tsd_separators, break_fonds_table, first_cleanse
from tk_functions import display_changelog, VerticalScrolledFrame, ListboxEditable
from patterns import lSupElements
import global_vars

# read config file, create if not found
Config = configparser.ConfigParser()
global_vars.working_folder = os.getcwd()
if os.path.exists(global_vars.working_folder + '/preproc_config.ini'):
    Config.read('preproc_config.ini')
    global_vars.opening_folder = Config['PATHS']['opening_dir']
    _version_ = Config['VERSION']['pre_proc_version']
    try:
        _current_version_ = urlopen('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/_version_.txt').read().decode('utf-8')
    except URLError:
        _current_version_ = _version_
        print('Could not check current version online. Check your internet connection! This doesnt affect the normal processing process!')
        global_vars.bFoundError = True
    if _version_ != _current_version_:
        global_vars.bUpToDate = False
        # get current update_script.py from github
        urlretrieve('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py',
                    filename=global_vars.working_folder + '/update_script.py')
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
    # big_fucking_table(tree)
    if global_vars.fReplaceNumbers.get():
        replace_number_list(tree, listboxNumbers2.return_list(), global_vars.lFalseNumberMatches, global_vars.report_path)
    if global_vars.fReplaceWords.get():
        replace_word_list(tree, listboxWords.return_list(), global_vars.lAllFalseWordMatches, global_vars.report_path)
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
    global_vars.tk.title('CoCo PreProcessor UI  --  ' + os.path.splitext(global_vars.tk.filename)[0])
    global_vars.tk.geometry('700x800')
    frameTop = Frame(global_vars.tk, height=3)
    frameTop.pack(side='top', fill='x')
    masterLabel = Label(frameTop,
                        text='Double Click on list entry to change entry OR\n'
                             'Navigate with ↑↓ between entries, open with ENTER',
                        width=55, font=('Arial', 10, 'bold'))
    masterLabel.pack(side='left')
    if not global_vars.bUpToDate:
        versionLabel = Label(frameTop,
                        text='New Version available!\n'
                             'Please update with update_script!',
                        width=30, font=('Arial', 9, 'bold'), fg='red')
        versionLabel.pack(side='right')
    else:
        changelogButton = Button(frameTop, text='Display Changelog', width=30, font=('Arial', 9), command=display_changelog)
        changelogButton.pack(side='left')

    # FRAME 1
    # this is not a common frame, it enables scrolling within a frame
    frameNumbers2 = VerticalScrolledFrame(global_vars.tk, width=150, height=50, borderwidth=2, relief="groove")
    frameNumbers2.pack(fill='y', side='left')
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    get_false_numbers(tree, global_vars.report_path)
    listboxNumbers2 = ListboxEditable(frameNumbers2, global_vars.lFalseNumberMatches, width=25)
    listboxNumbers2.placeListBoxEditable()

    # FRAME 2
    # this is not a common frame, it enables scrolling within a frame
    frameWords = VerticalScrolledFrame(global_vars.tk, width=250, height=50, borderwidth=2, relief="groove")
    frameWords.pack(fill='y', side='left', expand=True)
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    get_false_words(tree, global_vars.report_path)
    listboxWords = ListboxEditable(frameWords, global_vars.lAllFalseWordMatches, popup_menu=True ,width=45)
    listboxWords.placeListBoxEditable()

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
        fondsLabel = Label(frameChecks, text='Fonds report detected', font=('Arial', 9, 'bold'), fg='red')
        fondsLabel.pack(side='top')
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
if global_vars.bFoundError:
    input('Fix displayed errors and press ENTER to quit!')
