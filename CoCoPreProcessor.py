import re
import sys
import os
from tkinter import Tk, filedialog, Listbox, Label
from lxml import html, etree
from lxml.html.clean import Cleaner

def wrap(root, tag):
    # find <td> elements that do not have a <p> element
    cells = etree.XPath("//td[not(p)]")(root)
    for cell in cells:
        # Create new <p> element
        e = etree.Element(tag)
        # Set the <p> element text from the parent
        e.text = cell.text
        # Clear the parent text because it is now in the <p> element
        cell.text = None
        # Move the parents children and make them the <p> element's children
        # (because the span on line 10 of the input file should be nested)
        for child in cell.getchildren():
            # This actually moves the child from the <td> element to the <p> element
            e.append(child)
        # Set the new <p> element as the cell's child
        cell.append(e)

# File Dialog to choose htm-file
tk = Tk()
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
    # new = new.replace('\xa0', ' ')                                          # replaces non breaking spaces
    new = re.sub(r"(?sm)(?<=[a-z\,;\xa0])</p>\s*?<p>(?=[a-z])", ' ', new)  # removes wrong line breaks (BETA)
    fo.write(new)
    fo.close()

# open temp file for parsing
with open('tmp.htm', 'r+', encoding="utf-8") as input_file:
    tree = html.parse(input_file)

    # compile footnote patterns as regex object
    footnote_matches = [
        re.compile('\s*\d{1,2}\s*'),
        re.compile('\s*\*{1,9}\s*'),
        re.compile('\s*\*{1,9}\)\s*'),
        re.compile('\s*[a-z]\s*'),
        re.compile('\s*\d{1,2}\)\s*'),
        re.compile('\s*\(\d{1,2}\)\s*')
    ]

    # compile number format as regex objects
    number_formats = [
        re.compile('(^[-\s+(]{0,3}\d{1,3}\)?[ €%]{0,2}$)', re.MULTILINE),                        # 123 has to be first, to prevent double matches
        re.compile('(^[-\s+(]{0,3}\d{1,3}(\.\d{3})*?(,\d{1,5})?\)?[ €%]{0,2}$)', re.MULTILINE),  # 123.123,12000 ; 123,1 ; 123
        re.compile('(^[-\s+(]{0,3}\d{1,3}(,\d{3})*?(\.\d{1,5})?\)?[ €%]{0,2}$)', re.MULTILINE),  # 123,123.12 ; 123.1 ; 123
        re.compile('(^[-\s+(]{0,3}\d{1,3}(\s\d{3})*?(,\d{1,5})?\)?[ €%]{0,2}$)', re.MULTILINE),  # 123 123,12 ; 123,1 ; 123
        re.compile('(^[-\s+(]{0,3}\d{1,3}(\s\d{3})*?(\.\d{1,5})?\)?[ €%]{0,2}$)', re.MULTILINE), # 123 123.12 ; 123.1 ; 123
        # other allowed cell content
        re.compile('^[-.,\s]+$', re.MULTILINE),                                                  # empty cells and placeholder -,.
        re.compile('^\s*?(19|20)\d{2}\s*?$', re.MULTILINE),                                      # year 1900 - 2099
        re.compile('^\s*?[0123]?\d\.[0123]?\d\.(19|20)?\d{2}\s*?$', re.MULTILINE),               # dates 12.02.1991; 12.31.91: 12.31.2091
        re.compile('^.*[A-Za-z]{2,}.*$', re.DOTALL),                                              # text
        re.compile('^\s*?(T|Mio|Mrd|in)?\.?\s?[€$]\s*?$', re.MULTILINE)  # T€, Mio. €, Mrd. €, in €
    ]

    header_list = [
        number_formats[7],                                      # dates
        number_formats[6],                                      # year
        number_formats[9]                                       # T€, Mio. €, Mrd. €, in €
    ]

    unordered_list = [
        re.compile('^[►•] ', re.MULTILINE),
        re.compile('^- ', re.MULTILINE)
    ]

    # replace </p><p> in tables with <br>
    # takes the longest, might find better alternative
    for td in tree.xpath('//td[count(p)>1]'):
        i = 0;
        x = len(td)
        for p in range(x):
            i += 1
            if i > x - 1:
                break
            td.insert(p + i, etree.Element('br'))

    # remove sup/sub tags from headlines
    for e in tree.xpath(
            '/html/body/*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]/*[self::sup or self::sub]'):
        e.drop_tag()

    # remove p tags in tables
    for p in tree.xpath('//table//p'):
        # print(p.text)
        p.drop_tag()

    # remove li tags in td elements
    for li in tree.xpath('//td/li'):
        li.drop_tag()

    # remove empty table rows
    for row in tree.xpath('//tr[* and not(*[node()])]'):
        row.getparent().remove(row)

    # remove unwanted tags
    cleaner = Cleaner(
        remove_tags=['a', 'head', 'div'],
        style=True,
        meta=True,
        remove_unknown_tags=False,
        page_structure=False
    )
    tree = cleaner.clean_html(tree)

    tables = tree.xpath('//table')
    # check if tables are footnote tables
    for table in range(len(tables)):
        f_cells = []
        matches = []
        # print(len(tables[table].xpath('.//tr[1]/td')))
        # check first whether table is exactly 2 columns wide
        # print(table)
        if len(tables[table].xpath('.//tr[last()]/td')) == 2:
            # create list from first column values
            f_cells.append(tables[table].xpath('.//tr/td[1]'))
            # flatten list
            f_cells = [item for sublist in f_cells for item in sublist]
            # check if any footnote regex pattern matches, if yes set corresponding matches list value to true
            for element in f_cells:
                # remove sup, sub-tags if found
                for el in element:
                    if el.tag == 'sup' or el.tag == 'sub':
                        el.drop_tag()
                # create list with bool values of every regex, td-value match
                if element.text is not None:
                    matches.append(any(list(reg.fullmatch(element.text) for reg in footnote_matches)))
                else:
                    matches.append(False)
            # check if all footnote cell values matched with regex pattern
            if all(matches):
                # if yes set table attribute to "footnote" and insert anchors
                for element in f_cells:
                    etree.SubElement(element, 'a', id='a' + str(table + 1) + str(f_cells.index(element)))
                tables[table].set('class', 'footnote')
            # clear lists
            f_cells.clear()
            matches.clear()

    # check numbers in table cells
    # get all tables that are not footnote tables
    std_tables = tree.xpath('//table[not(@class="footnote")]')
    undef_matches = []
    for table in std_tables:
        subtable = []
        format_count = [0] * len(number_formats)
        # select all non-empty td-elements, beginning at second column
        subtable.append(table.xpath('.//tr/td[position() > 1]'))
        for row in subtable:
            for cell in row:
                cell_format = [0] * len(number_formats)
                for i in range(len(number_formats)):
                    # breaks after first match
                    if cell.text is not None and number_formats[i].fullmatch(str(cell.text)):
                        cell_format[i] += 1
                        break
                if sum(cell_format):
                    format_count = [a + b for a, b in zip(format_count, cell_format)]
                else:
                    undef_matches.append(cell.text)

    # set table headers row for row
    for table in std_tables:
        header_flag = False
        header_rows = -1    # -1 for later comparison with 0 index
        for row in table:
            for cell in row:
                if cell.text is not None:
                    if any(list(reg.fullmatch(cell.text) for reg in header_list)):
                        header_flag = True
                        header_rows = table.index(row)
                    if any(list(reg.fullmatch(cell.text) for reg in number_formats[0:4])):
                        # print('found number')
                        header_rows = old
                        break
            old = header_rows

        # get the first occuring row in which the first cell is not empty
        first_textrow = table.xpath('./tr[td[position() = 1 and text()]][1]')
        if len(first_textrow):
            # index of the first cell with text - 1 to get only empty cells
            text_cell_row = table.index(first_textrow[0]) - 1
            if header_rows <= text_cell_row:
                header_rows = text_cell_row
                header_flag = True

        if header_flag:
            # create lists with header and body elements
            # this is needed at the beginning, because the position changes when adding header and body tags
            headers = table.xpath('.//tr[position() <= %s]' % str(header_rows + 1))
            body = table.xpath('.//tr[position() > %s]' % str(header_rows + 1))
            # create thead-/tbody-tags
            table.insert(0, etree.Element('tbody'))
            table.insert(0, etree.Element('thead'))

            # move rows to inside header or body
            for thead in headers:
                table.find('thead').append(thead)
            for tbody in body:
                table.find('tbody').append(tbody)

    # find and set unordered lists
    dash_list = []
    dash_count = 0
    for p in tree.xpath('//body/p'):
        # check if beginning of paragraph matches safe list denominators (no -)
        if p.text:
            if unordered_list[0].match(p.text):
                p.text = unordered_list[0].sub('', p.text)
                p.tag = 'li'
            # if not check if "- " matches
            elif unordered_list[1].match(p.text):
                dash_count += 1
                # append to list for later tag change
                dash_list.append(p)
            else:
                # if only one dash is present, remove last element from dash list (single list item could be confused with
                # wrong break)
                if dash_count == 1:
                    dash_list.pop()
                dash_count = 0
    # iterate through dash list and change to unordered list
    for p in dash_list:
        p.text = unordered_list[1].sub('', p.text)
        p.tag = 'li'

    # wrap all table contents in p-tags
    wrap(tree, "p")
    # write to new file in source folder
    tree.write(os.path.splitext(tk.filename)[0] + '_modified.htm', encoding='UTF-8', method='html')

os.remove('tmp.htm')  # remove original

# UI for number checks
def listbox_copy(lb):
    tk.clipboard_clear()
    w = lb.widget
    selected = int(w.curselection()[0])
    tk.clipboard_append(w.get(selected))

if len(undef_matches) is not 0:
    tk.title('False formatted numbers')
    label = Label(tk, text='Double Click to copy')
    label.pack()
    undef_MSB = Listbox(tk, width=40)
    for e in range(len(undef_matches)):
        undef_MSB.insert(e, undef_matches[e])
    undef_MSB.pack()
    undef_MSB.bind('<Double-Button-1>', listbox_copy)
    tk.mainloop()