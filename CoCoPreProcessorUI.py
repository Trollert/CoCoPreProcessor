#!/usr/bin/python
import sys
import re
import os
from functools import partial
from tkinter import filedialog, Label, Frame, Entry, Button, Checkbutton, messagebox
from lxml import html
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError
import configparser

# custom imports
try:
    from functions import span_cleanup, post_cleanup, add_to_errorlog, split_rowspan, big_fucking_table, replace_word_list, replace_number_list, set_footnote_tables, get_false_words, get_false_numbers, set_headers, set_unordered_list, remove_empty_rows, merge_tables_vertically, sup_elements, set_span_headers, rename_pictures, fix_tsd_separators, break_fonds_table, pre_cleanup
    from tk_functions import display_changelog, VerticalScrolledFrame, ListboxEditable
    from patterns import lSupElements
    import global_vars
except ImportError:
    urlretrieve('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py',
                filename=os.getcwd() + '/update_script.py')
    messagebox.showerror('Warning', 'Some modules could not be found! \n\nUpdate manually by clicking update_script.py!')
    sys.exit()


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
        add_to_errorlog('Could not check current version online. Check your internet connection! This doesnt affect the normal processing process!')
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

global_vars.tk.filename = filedialog.askopenfilename(initialdir=global_vars.opening_folder, title="Select file",
                                                     filetypes=(("HTML files", "*.htm"), ("all files", "*.*")))
global_vars.report_path = os.path.dirname(global_vars.tk.filename)
if not global_vars.tk.filename: sys.exit()

# open the file as string, to replace tag-based substrings
# much easier to do before parsing html
with open(global_vars.tk.filename, 'r', encoding='UTF-8') as fi, \
        open('tmp.htm', 'w', encoding='UTF-8') as fo:
    new_str = fi.read()
    new = new_str.replace('CO2', 'CO<sub>2</sub>')  # replaces every occurrence of CO2
    new = new.replace('—', '-')  # replaces en dash with normal dash
    # new = new.replace('\u2013', '-')  # replaces en dash with normal dash
    new = new.replace('&nbsp;', ' ')  # replaces non breaking spaces
    # REMOVE WRONG LINE BREAK HERE BECAUSE I CANT FIGURE OUT HOW TO DO IT WITHIN THE PARSER
    new = re.sub(r"(?sm)(?<=[a-zöüä\,;\xa0])\s*?</p>\s*?<p>(?=[a-zöäü][^)])", ' ', new)
    fo.write(new)
    fo.close()


    ################
    # PARSING FILE #
    ################
def generate_file(entryCkb):
    if global_vars.bSpanHeaders.get():
        set_span_headers()
        span_cleanup()
    if global_vars.bRemoveEmptyRows.get():
        remove_empty_rows()
    if global_vars.bMergeTablesVertically.get():
        merge_tables_vertically()
    if global_vars.bSplitRowspan.get():
        split_rowspan()
    if global_vars.bReplaceNumbers.get():
        replace_number_list(listboxNumbers.return_list(), global_vars.lFalseNumberMatches)
    if global_vars.bReplaceWords.get():
        replace_word_list(listboxWords.return_list(), global_vars.lAllFalseWordMatches)
    if global_vars.bSetUnorderedList.get():
        set_unordered_list()
    if global_vars.bFootnotetables.get():
        set_footnote_tables()
    if global_vars.bSetHeaders.get():
        set_headers()
    if global_vars.fIsFondsReport.get():
        if global_vars.bFixTsdSeparators.get():
            fix_tsd_separators(',')
        if global_vars.bBreakFondsTable.get():
            break_fonds_table()
    if global_vars.bRenamePictures.get():
        rename_pictures()

    if global_vars.bFoundError:
        messagebox.showwarning('Warning', '\n'.join(global_vars.lsErrorLog))

    post_cleanup(entryCkb)

    global_vars.tk.destroy()


with open('tmp.htm', 'r+', encoding="utf-8") as input_file:
    global_vars.tree = html.parse(input_file)
    pre_cleanup()
    ############
    # BUILD UI #
    ############

    # MASTER WINDOW
    global_vars.tk.title('CoCo PreProcessor UI v. ' + Config['VERSION']['pre_proc_version'] + ' --  ' + os.path.splitext(global_vars.tk.filename)[0])
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
    frameNumbers = VerticalScrolledFrame(global_vars.tk, width=150, height=50, borderwidth=2, relief="groove")
    frameNumbers.pack(fill='y', side='left')
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    get_false_numbers(global_vars.report_path)
    listboxNumbers = ListboxEditable(frameNumbers, global_vars.lFalseNumberMatches, width=25)
    listboxNumbers.placeListBoxEditable()

    # FRAME 2
    # this is not a common frame, it enables scrolling within a frame
    frameWords = VerticalScrolledFrame(global_vars.tk, width=250, height=50, borderwidth=2, relief="groove")
    frameWords.pack(fill='y', side='left', expand=True)
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    get_false_words(global_vars.report_path)
    listboxWords = ListboxEditable(frameWords, global_vars.lAllFalseWordMatches, popup_menu=True, width=45)
    listboxWords.placeListBoxEditable()

    # FRAME 3
    frameChecks = Frame(global_vars.tk, width=25, height=50)
    frameChecks.pack(fill='y', side='left')
    ckbHeaders = Checkbutton(frameChecks, anchor='w', text='convert headers', variable=global_vars.bSetHeaders)
    ckbFootnotes = Checkbutton(frameChecks, anchor='w', text='convert footnotes', variable=global_vars.bFootnotetables)
    ckbEmptyRows = Checkbutton(frameChecks, anchor='w', text='remove empty rows', variable=global_vars.bRemoveEmptyRows)
    ckbWords = Checkbutton(frameChecks, anchor='w', text='replace fixed words', variable=global_vars.bReplaceWords)
    ckbNumbers = Checkbutton(frameChecks, anchor='w', text='replace fixed numbers', variable=global_vars.bReplaceNumbers)
    ckbVertMerge = Checkbutton(frameChecks, anchor='w', text='vertically merge tables (§§)',
                               variable=global_vars.bMergeTablesVertically)
    if global_vars.bIsFormatted:
        ckbSpanHeaders = Checkbutton(frameChecks, anchor='w', text='analyze heading (BETA)', variable=global_vars.bSpanHeaders)
    ckbRenamePics = Checkbutton(frameChecks, anchor='w', text='rename .png to .jpg', variable=global_vars.bRenamePictures)
    ckbSplitRowspan = Checkbutton(frameChecks, anchor='w', text='split row span', variable=global_vars.bSplitRowspan)
    ckbSetUnorderedLists = Checkbutton(frameChecks, anchor='w', text='set unordered lists', variable=global_vars.bSetUnorderedList)
    ckbIndentUnorderedLists = Checkbutton(frameChecks, anchor='w', text='Indent unordered lists?', variable=global_vars.bIndentUnorderedList)

    ckbHeaders.pack(side='top', anchor='w')
    ckbFootnotes.pack(side='top', anchor='w')
    ckbEmptyRows.pack(side='top', anchor='w')
    ckbWords.pack(side='top', anchor='w')
    ckbNumbers.pack(side='top', anchor='w')
    ckbVertMerge.pack(side='top', anchor='w')
    if global_vars.bIsFormatted:
        ckbSpanHeaders.pack(side='top', anchor='w')
    ckbRenamePics.pack(side='top', anchor='w')
    ckbSplitRowspan.pack(side='top', anchor='w')
    ckbSetUnorderedLists.pack(side='top', anchor='w')
    ckbIndentUnorderedLists.pack(side='top')

    # Sup check button
    labelCkb = Label(frameChecks, text='\nSuperscript elements')
    labelCkb.pack(side='top', anchor='w')
    frameCkb = Frame(frameChecks, width=25, height=5)
    frameCkb.pack(side='top')
    ckbSup = Checkbutton(frameCkb, anchor='w', variable=global_vars.bSupElements)
    ckbSup.pack(side='left', anchor='w')
    entryCkb = Entry(frameCkb, width=23, )
    entryCkb.insert(0, ', '.join(lSupElements))
    entryCkb.pack(side='left')

    if global_vars.fIsFondsReport.get():
        fondsLabel = Label(frameChecks, text='Fonds report detected', font=('Arial', 9, 'bold'), fg='red')
        fondsLabel.pack(side='top')
        ckbTsdFix = Checkbutton(frameChecks, anchor='w', text='fix tsd separators', variable=global_vars.bFixTsdSeparators)
        ckbBreakFondsTable = Checkbutton(frameChecks, anchor='w', text='break Vermögensaufstellung', variable=global_vars.bBreakFondsTable)
        ckbTsdFix.pack(side='top', anchor='w')
        ckbBreakFondsTable.pack(side='top', anchor='w')

    buttonGenerate = Button(frameChecks, height=3, width=20, bd=2, fg='white', font=('Arial', 15),
                            text='GENERATE FILE \n AND QUIT', command=partial(generate_file, entryCkb),
                            bg='dark green')
    buttonGenerate.pack(side='bottom')
    global_vars.tk.mainloop()

os.remove('tmp.htm')  # remove original
# if global_vars.bFoundError:
#     input('Fix displayed errors and press ENTER to quit!')
