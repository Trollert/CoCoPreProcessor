#!/usr/bin/env python3
import sys
import os
from functools import partial
from tkinter import filedialog, Label, Frame, Entry, Button, Checkbutton, messagebox
from lxml import html
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError
import configparser

# custom imports
try:
    from functions import remove_false_text_breaks, span_cleanup, post_cleanup, add_to_error_log, split_rowspan, big_fucking_table, replace_word_list, replace_number_list, set_footnote_tables, get_false_words, get_false_numbers, set_headers, set_unordered_list, remove_empty_rows, merge_tables_vertically, sup_elements, set_span_headers, rename_pictures, fix_tsd_separators, break_fonds_table, pre_cleanup
    from tk_functions import display_changelog, VerticalScrolledFrame, ListboxEditable
    from patterns import lSupElements
    import global_vars as gv
except ImportError:
    urlretrieve('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/update_script.py',
                filename=os.getcwd() + '/update_script.py')
    messagebox.showerror('Warning', 'Some modules could not be found! \n\nUpdate manually by clicking update_script.py!')
    sys.exit()


# read config file, create if not found
Config = configparser.ConfigParser()
gv.path_root_UI = os.getcwd()
if os.path.exists(gv.path_root_UI + '/preproc_config.ini'):
    Config.read('preproc_config.ini')
    gv.path_folder_user = Config['PATHS']['opening_dir']
    _version_ = Config['VERSION']['pre_proc_version']
    try:
        _current_version_ = urlopen('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/_version_.txt').read().decode('utf-8')
    except URLError:
        _current_version_ = _version_
        add_to_error_log('Could not check current version online. Check your internet connection! This doesnt affect the normal processing process!')
        gv.flag_found_error = True
    if _version_ != _current_version_:
        gv.flag_up_to_date = False
        # get current update_script.py from github

else:
    print('No config file found, update script with update_script.py and restart'
          ' CoCoPreProcessorUI.py before proceeding! This message will still appear though, so dont get confused')

    Config['PATHS'] = {}
    Config['PATHS']['opening_dir'] = filedialog.askdirectory(title='Choose the directory to open when using CoCo-PreProcessor!')
    workingFolder = Config['PATHS']['opening_dir']
    Config['VERSION'] = {}
    Config['VERSION']['pre_proc_version'] = urlopen('https://raw.githubusercontent.com/Trollert/CoCoPreProcessor/master/_version_.txt').read().decode('utf-8')
    with open(gv.path_root_UI + '/preproc_config.ini', 'w') as configfile:
        Config.write(configfile)

#####################
#     OPEN FILE     #
#####################

gv.tk.filename = filedialog.askopenfilename(initialdir=gv.path_folder_user, title="Select file",
                                            filetypes=(("HTML files", "*.htm"), ("all files", "*.*")))
gv.path_report = os.path.dirname(gv.tk.filename)
if not gv.tk.filename: sys.exit()

# open the file as string, to replace tag-based substrings
# much easier to do before parsing html
with open(gv.tk.filename, 'r', encoding='UTF-8') as fi, \
        open('tmp.htm', 'w', encoding='UTF-8') as fo:
    new_str = fi.read()
    new = new_str.replace('CO2', 'CO<sub>2</sub>')  # replaces every occurrence of CO2
    new = new.replace('–', '-')
    new = new.replace('—', '-')  # replaces en dash with normal dash
    # new = new.replace('\u2013', '-')  # replaces en dash with normal dash
    new = new.replace('&nbsp;', ' ')  # replaces non breaking spaces
    # REMOVE WRONG LINE BREAK HERE BECAUSE I CANT FIGURE OUT HOW TO DO IT WITHIN THE PARSER
    # new = re.sub(r"(?sm)(?<=[a-zöüä\,;\xa0])\s*?</p>\s*?<p>(?=[a-zöäü][^)])", ' ', new)
    fo.write(new)
    fo.close()


    ################
    # PARSING FILE #
    ################
def generate_file(entryCkb):
    if gv.b_remove_false_text_breaks.get():
        remove_false_text_breaks()
    if gv.b_span_headings.get():
        set_span_headers()
        span_cleanup()
    if gv.b_merge_tables_vertically.get():
        merge_tables_vertically()
    if gv.b_split_rowspan.get():
        split_rowspan()
    if gv.b_remove_empty_rows.get():
        remove_empty_rows()
    # big_fucking_table()
    replace_number_list(ListboxNumbers.return_list(), gv.list_false_number_matches)
    replace_word_list(ListboxWords.return_list(), gv.list_false_word_matches)
    if gv.b_set_unordered_lists.get():
        set_unordered_list()
    if gv.b_set_footnotes.get():
        set_footnote_tables()
    if gv.b_set_headers.get():
        set_headers()
    if gv.b_fonds_report.get():
        if gv.b_fix_tsd_separators.get():
            fix_tsd_separators(',')
        if gv.b_break_fonds_table.get():
            break_fonds_table()
    if gv.b_rename_pics.get():
        rename_pictures()

    if gv.flag_found_error:
        messagebox.showwarning('Warning', '\n'.join(gv.list_error_log))

    post_cleanup(entryCkb)

    gv.tk.destroy()


with open('tmp.htm', 'r+', encoding="utf-8") as input_file:
    gv.tree = html.parse(input_file)
    pre_cleanup()
    ############
    # BUILD UI #
    ############

    # MASTER WINDOW
    gv.tk.title('CoCo PreProcessor UI v. ' + Config['VERSION']['pre_proc_version'] + ' --  ' + os.path.splitext(gv.tk.filename)[0])
    print(gv.tk.filename)
    gv.tk.geometry('700x800')
    FrameTopMaster = Frame(gv.tk, height=3)
    FrameTopMaster.pack(side='top', fill='x')
    MasterLabel = Label(FrameTopMaster,
                        text='Double Click on list entry to change entry OR\n'
                             'Navigate with ↑↓ between entries, open with ENTER',
                        width=55, font=('Arial', 10, 'bold'))
    MasterLabel.pack(side='left')
    if not gv.flag_up_to_date:
        VersionLabel = Label(FrameTopMaster,
                             text='New Version available!\n'
                             'Please update with update_script!',
                             width=30, font=('Arial', 9, 'bold'), fg='red')
        VersionLabel.pack(side='right')
    else:
        ChangelogButton = Button(FrameTopMaster, text='Display Changelog', width=30, font=('Arial', 9), command=display_changelog)
        ChangelogButton.pack(side='left')

    # FRAME 1
    # this is not a common frame, it enables scrolling within a frame
    FrameNumbers = VerticalScrolledFrame(gv.tk, width=150, height=50, borderwidth=2, relief="groove")
    FrameNumbers.pack(fill='y', side='left')
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    get_false_numbers(gv.path_report)
    ListboxNumbers = ListboxEditable(FrameNumbers, gv.list_false_number_matches, width=25)
    ListboxNumbers.placeListBoxEditable()

    # FRAME 2
    # this is not a common frame, it enables scrolling within a frame
    FrameWords = VerticalScrolledFrame(gv.tk, width=250, height=50, borderwidth=2, relief="groove")
    FrameWords.pack(fill='y', side='left', expand=True)
    # LISTBOX 2
    # this is not a real listbox, its a frame with sublabels to enable inline editing
    get_false_words(gv.path_report)
    ListboxWords = ListboxEditable(FrameWords, gv.list_false_word_matches, popup_menu=True, width=45)
    ListboxWords.placeListBoxEditable()

    # FRAME 3
    FrameChecks = Frame(gv.tk, width=25, height=50)
    FrameChecks.pack(fill='y', side='left')
    CheckboxHeaders = Checkbutton(FrameChecks, anchor='w', text='convert headers', variable=gv.b_set_headers)
    CheckboxFootnotes = Checkbutton(FrameChecks, anchor='w', text='convert footnotes', variable=gv.b_set_footnotes)
    CheckboxEmptyRows = Checkbutton(FrameChecks, anchor='w', text='remove empty rows', variable=gv.b_remove_empty_rows)
    CheckboxFalseTextBreaks = Checkbutton(FrameChecks, anchor='w', text='remove false text breaks', variable=gv.b_remove_false_text_breaks)
    CheckboxVerticalMerge = Checkbutton(FrameChecks, anchor='w', text='vertically merge tables (§§)',
                                        variable=gv.b_merge_tables_vertically)
    if gv.flag_is_formatted:
        CheckboxSpanHeaders = Checkbutton(FrameChecks, anchor='w', text='analyze heading (BETA)', variable=gv.b_span_headings)
    CheckboxRenamePics = Checkbutton(FrameChecks, anchor='w', text='rename .png to .jpg', variable=gv.b_rename_pics)
    CheckboxSplitRowspan = Checkbutton(FrameChecks, anchor='w', text='split row span', variable=gv.b_split_rowspan)
    CheckboxSetUnorderedLists = Checkbutton(FrameChecks, anchor='w', text='set unordered lists', variable=gv.b_set_unordered_lists)
    CheckboxIndentUnorderedLists = Checkbutton(FrameChecks, anchor='w', text='Indent unordered lists?', variable=gv.b_indent_unordered_list)

    CheckboxHeaders.pack(side='top', anchor='w')
    CheckboxFootnotes.pack(side='top', anchor='w')
    CheckboxEmptyRows.pack(side='top', anchor='w')
    CheckboxFalseTextBreaks.pack(side='top', anchor='w')
    CheckboxVerticalMerge.pack(side='top', anchor='w')
    if gv.flag_is_formatted:
        CheckboxSpanHeaders.pack(side='top', anchor='w')
    CheckboxRenamePics.pack(side='top', anchor='w')
    CheckboxSplitRowspan.pack(side='top', anchor='w')
    CheckboxSetUnorderedLists.pack(side='top', anchor='w')
    CheckboxIndentUnorderedLists.pack(side='top')

    # Sup check button
    LabelSupCheckbox = Label(FrameChecks, text='\nSuperscript elements')
    LabelSupCheckbox.pack(side='top', anchor='w')
    FrameSupCheckbox = Frame(FrameChecks, width=25, height=5)
    FrameSupCheckbox.pack(side='top')
    CheckboxSup = Checkbutton(FrameSupCheckbox, anchor='w', variable=gv.b_sup_elements)
    CheckboxSup.pack(side='left', anchor='w')
    EntrySup = Entry(FrameSupCheckbox, width=23, )
    EntrySup.insert(0, ', '.join(lSupElements))
    EntrySup.pack(side='left')

    if gv.b_fonds_report.get():
        LabelFondsReport = Label(FrameChecks, text='Fonds report detected', font=('Arial', 9, 'bold'), fg='red')
        LabelFondsReport.pack(side='top')
        CheckboxTsdFix = Checkbutton(FrameChecks, anchor='w', text='fix tsd separators', variable=gv.b_fix_tsd_separators)
        CheckboxBreakFondsTable = Checkbutton(FrameChecks, anchor='w', text='break Vermögensaufstellung', variable=gv.b_break_fonds_table)
        CheckboxTsdFix.pack(side='top', anchor='w')
        CheckboxBreakFondsTable.pack(side='top', anchor='w')

    ButtonGenerate = Button(FrameChecks, height=3, width=20, bd=2, fg='white', font=('Arial', 15),
                            text='GENERATE FILE \n AND QUIT', command=partial(generate_file, EntrySup),
                            bg='dark green')
    ButtonGenerate.pack(side='bottom')
    gv.tk.mainloop()

os.remove('tmp.htm')  # remove original
# if gv.bFoundError:
#     input('Fix displayed errors and press ENTER to quit!')
