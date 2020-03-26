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
        re.compile('(^[-\s+]{0,2}\d{1,3}$)', re.MULTILINE),  # 123 has to be first, to prevent double matches
        re.compile('(^[-\s+]{0,2}\d{1,3}(\.\d{3})*?(,\d{1,2})?$)', re.MULTILINE),  # 123.123,12 ; 123,1 ; 123
        re.compile('(^[-\s+]{0,2}\d{1,3}(,\d{3})*?(\.\d{1,2})?$)', re.MULTILINE),  # 123,123.12 ; 123.1 ; 123
        re.compile('(^[-\s+]{0,2}\d{1,3}(\s\d{3})*?(,\d{1,2})?$)', re.MULTILINE),  # 123 123,12 ; 123,1 ; 123
        re.compile('(^[-\s+]{0,2}\d{1,3}(\s\d{3})*?(\.\d{1,2})?$)', re.MULTILINE),  # 123 123.12 ; 123.1 ; 123
        # other allowed cell content
        re.compile('^[-.,\s]+$', re.MULTILINE),  # empty cells and placeholder -,.
        re.compile('^(19|20)\d{2}$', re.MULTILINE),  # year 1900 - 2099
        re.compile('^.*[A-Za-z]{2,}.*$', re.DOTALL)
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
        # subtable.append(table.xpath('.//tbody/tr/td[position() > 1 and string-length(text()) > 0]'))
        subtable.append(table.xpath('.//tbody/tr/td[position() > 1]'))  # ignores thead content
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

        # print('Table nr.: ' + str(std_tables.index(table)))
        # print('Number format of table: ' + str(format_count.index(max(format_count[1:4]))))
        # print('Nr. of Matches:')
        # print('123:\t\t' + str(format_count[0]))
        # print('123.123,12:\t' + str(format_count[1]))
        # print('123,123.12:\t' + str(format_count[2]))
        # print('123 123,12:\t' + str(format_count[3]))
        # print('123 123.12:\t' + str(format_count[4]))
        # print('.,- :\t\t' + str(format_count[5]))
        # print('Year/Date:\t' + str(format_count[6]))
        # print('Text:\t\t' + str(format_count[7]))
        # # print('No match:\t' + str(format_count[8]))
        # print('--------------------------\n')

        # print(cell.xpath('count(./preceding-sibling::td) + 1'), end=' ')

    # wrap all table contents in p-tags
    wrap(tree, "p")
    # write to new file in source folder
    tree.write(os.path.splitext(tk.filename)[0] + '_modified.htm', encoding='UTF-8', method='html')

os.remove('tmp.htm')  # remove original


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
