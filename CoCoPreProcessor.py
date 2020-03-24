<<<<<<< HEAD
import fileinput
import re
import sys
import os
from tkinter import Tk, filedialog
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

with fileinput.FileInput(tk.filename, inplace=True) as file:
    for line in file:
        print(line.replace('CO2', 'CO<sub>2</sub>'), end='')

with open(tk.filename, 'r+', encoding="utf-8") as input_file:

    tree = html.parse(input_file)

    # compile footnote patterns as regex object
    footnote_matches = [
        re.compile('\s*\d{1,2}\s*'),
        re.compile('\s*\*{1,9}\s*'),
        re.compile('\s*\*{1,9}\)\s*'),
        re.compile('\s*[a-z]\s*')
    ]

    # replace </p><p> in tables with <br>
    # takes the longest, might find better alternative
    for td in tree.xpath('//td[count(p)>1]'):
        i = 0;
        x = len(td)
        for p in range(x):
            i += 1
            if i > x-1:
                break
            td.insert(p+i, etree.Element('br'))

    # remove sup/sub tags from headlines
    for e in tree.xpath('/html/body/*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]/*[self::sup or self::sub]'):
        e.drop_tag()

    # remove p tags in tables
    for p in tree.xpath('//table//p'):
        # print(p.text)
        p.drop_tag()

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
    # wrap all table contents in p-tags
    wrap(tree, "p")
    # write to new file in source folder
    tree.write(os.path.splitext(input_file.name)[0] + '_modified.htm', encoding='UTF-8', method='html')



=======
import fileinput
import re
import sys
import os
from tkinter import Tk, filedialog
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

with fileinput.FileInput(tk.filename, inplace=True) as file:
    for line in file:
        print(line.replace('CO2', 'CO<sub>2</sub>'), end='')

with open(tk.filename, 'r+', encoding="utf-8") as input_file:

    tree = html.parse(input_file)

    # compile footnote patterns as regex object
    footnote_matches = [
        re.compile('\s*\d{1,2}\s*'),
        re.compile('\s*\*{1,9}\s*'),
        re.compile('\s*\*{1,9}\)\s*'),
        re.compile('\s*[a-z]\s*')
    ]

    # replace </p><p> in tables with <br>
    # takes the longest, might find better alternative
    for td in tree.xpath('//td[count(p)>1]'):
        i = 0;
        x = len(td)
        for p in range(x):
            i += 1
            if i > x-1:
                break
            td.insert(p+i, etree.Element('br'))

    # remove sup/sub tags from headlines
    for e in tree.xpath('/html/body/*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]/*[self::sup or self::sub]'):
        e.drop_tag()

    # remove p tags in tables
    for p in tree.xpath('//table//p'):
        # print(p.text)
        p.drop_tag()

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
    # wrap all table contents in p-tags
    wrap(tree, "p")
    # write to new file in source folder
    tree.write(os.path.splitext(input_file.name)[0] + '_modified.htm', encoding='UTF-8', method='html')



>>>>>>> 54d4897ac0dd26d60056da4f7d5601477f47f43e
