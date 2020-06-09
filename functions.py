import pickle

from lxml import etree
from lxml.html.clean import Cleaner
from textwrap import wrap as text_wrap
import global_vars
from patterns import *
import os
from dateutil import parser

# configure german for dateutil parser
class GermanParserInfo(parser.parserinfo):
    WEEKDAYS = [("Mo.", "Montag"),
                ("Di.", "Dienstag"),
                ("Mi.", "Mittwoch"),
                ("Do.", "Donnerstag"),
                ("Fr.", "Freitag"),
                ("Sa.", "Samstag"),
                ("So.", "Sonntag")]
    MONTHS = [("Jan.", "Januar"),
              ("Feb.", "Februar"),
              ("März", "März"),
              ("Apr.", "April"),
              ("Mai", "Mai"),
              ("Jun.", "Juni"),
              ("Jul.", "Juli"),
              ("Aug.", "August"),
              ("Sept.", "September"),
              ("Okt.", "Oktober"),
              ("Nov.", "November"),
              ("Dez.", "Dezember")]

######################
# OPTIONAL FUNCTIONS #
######################

def replace_word_list(replace_list, old_list):
    """
    replace the corrected listbox items with their counterparts
    """

    leTextElements = global_vars.tree.xpath('.//*[normalize-space(text())]')
    # get a list of listbox lines
    corrected_list = list(replace_list)

    # create duplicate to not create confusion while popping
    tempAllFalseWords = old_list

    # remove unaffected entries from both lists
    for idx in reversed(range(len(tempAllFalseWords))):
        if tempAllFalseWords[idx] == corrected_list[idx]:
            tempAllFalseWords.pop(idx)
            corrected_list.pop(idx)

    # create file to safe already replaced words in case of error
    save_replacements(dict(zip(tempAllFalseWords, corrected_list)), '/save_words.pkl')

    for e in leTextElements:
        for repEl in range(len(corrected_list)):
            if e.text:
                e.text = e.text.replace(tempAllFalseWords[repEl], corrected_list[repEl])


def replace_number_list(replace_list, old_list):
    leNumberElements = global_vars.tree.xpath('//table[not(@class="footnote")]/tr/td[normalize-space(text())]')
    # get a list of listbox lines
    temp_list = replace_list
    tempAllfalseNumbers = old_list
    for idx in reversed(range(len(tempAllfalseNumbers))):
        if tempAllfalseNumbers[idx] == temp_list[idx]:
            tempAllfalseNumbers.pop(idx)
            temp_list.pop(idx)

    # create file to safe already replaced numbers in case of error
    save_replacements(dict(zip(tempAllfalseNumbers, temp_list)), '/save_numbers.pkl')

    for e in leNumberElements:
        for repEl in range(len(temp_list)):
            if e.text:
                e.text = e.text.replace(tempAllfalseNumbers[repEl], temp_list[repEl])


def set_footnote_tables():
    leAllTables = global_vars.tree.xpath('//table')
    # check if tables are footnote tables
    for table in range(len(leAllTables)):
        leFirstColCells = []
        lbFootnoteMatches = []
        # print(len(tables[table].xpath('.//tr[1]/td')))
        # check first whether table is exactly 2 columns wide
        # print(table)
        if len(leAllTables[table].xpath('.//tr[last()]/td')) == 2:
            # create list from first column values
            leFirstColCells.append(leAllTables[table].xpath('.//tr/td[1]'))
            # flatten list
            leFirstColCells = [item for sublist in leFirstColCells for item in sublist]
            # check if any footnote regex pattern matches, if yes set corresponding matches list value to true
            for eCell in leFirstColCells:
                # remove sup, sub-tags if found
                for el in eCell:
                    if el.tag == 'sup' or el.tag == 'sub':
                        el.drop_tag()
                # create list with bool values of every regex, td-value match
                if eCell.text is not None:
                    lbFootnoteMatches.append(any(list(reg.fullmatch(eCell.text) for reg in regFootnote)))
                else:
                    lbFootnoteMatches.append(False)
            # check if all footnote cell values matched with regex pattern
            if all(lbFootnoteMatches):
                # if yes set table attribute to "footnote" and insert anchors
                for eCell in leFirstColCells:
                    etree.SubElement(eCell, 'a', id='a' + str(table + 1) + str(leFirstColCells.index(eCell)))
                leAllTables[table].set('class', 'footnote')

            # clear lists
            leFirstColCells.clear()
            lbFootnoteMatches.clear()


def get_false_numbers(path):
    # check numbers in table cells
    # get all tables that are not footnote tables
    leStandardTables = global_vars.tree.xpath('//table[not(@class="footnote")]')
    # if save numbers file exists, replace matches before finding new ones
    if os.path.exists(path + '/save_numbers.pkl'):
        save_file = open(path + '/save_numbers.pkl', 'rb')
        save_dict = pickle.load(save_file)
        save_file.close()
        for table in leStandardTables:
            for row in table:
                for cell in row:
                    if cell.text is not None:
                        for old, new in save_dict.items():
                            cell.text = cell.text.replace(old, new)

    for table in leStandardTables:
        leSubtables = []
        iFormatCount = [0] * (len(regNumbers) + 1)
        # select all non-empty td-elements, beginning at second column
        leSubtables.append(table.xpath('.//tr/td[position() > 1 and normalize-space(text())]'))
        for row in leSubtables:
            for cell in row:
                # trim leading/trailing whitespace (not sure why its done here)
                # cell.text = cell.xpath('normalize-space(text())')
                if cell.text:
                    cell_format = [0] * len(regNumbers)
                    for i in range(len(regNumbers)):
                        # breaks after first match to count what format the number was displayed
                        if cell.text and regNumbers[i].fullmatch(str(cell.text)):
                            cell_format[i] += 1
                            break
                    # TODO: Make this date br matching better
                    # stupid hacky shit to check cells with br-tag for date matching
                    cellWithoutBr = ''
                    if cell.find('br') is not None:
                        brAll = cell.findall('br')
                        cellWithoutBr = cell.text
                        for br in brAll:
                            cellWithoutBr += ' ' + br.tail
                    if cellWithoutBr:
                        cellWithoutBr = re.sub(r'(\t|\n)', '', cellWithoutBr)

                    # if any format matched increase the table counter and dont change anything
                    if sum(cell_format):
                        iFormatCount = [a + b for a, b in zip(iFormatCount, cell_format)]
                    # if br-tags where present within the cell, check that first
                    elif cellWithoutBr and is_date(cellWithoutBr, False)[0]:
                        iFormatCount[-1] += 1
                    # if not check normally
                    elif is_date(cell.text, False)[0]:
                        iFormatCount[-1] += 1
                        if is_date(cell.text, False)[1]:
                            cell.text = re.sub('\s', '', cell.text)
                    elif any(reg.fullmatch(cell.text) for reg in regMisc + regHeaderContent):
                        continue
                    # if no match could be found, try to fix it or move it to false match list
                    else:
                        if global_vars.bFixNumbers.get():
                            # if cell only contains number tokens, try to fix format
                            if re.fullmatch('[0-9,. \-+]*', cell.text_content()):
                                # drop br-tag if one is found
                                if cell.find('br'):
                                    cell.find('br').drop_tag()
                                # if, after removing whitespace, the resulting format matches a number format,
                                # remove the whitespace from tree element
                                if any(list(reg.fullmatch(re.sub(r'\s+', '', cell.text)) for reg in regNumbers)):
                                    cell.text = re.sub(r'\s+', '', cell.text)
                                # if you cant fix it, append to false number list
                                else:
                                    global_vars.lFalseNumberMatches.append(cell.text)
                            # otherwise append it to false number match list
                            else:
                                global_vars.lFalseNumberMatches.append(cell.text)
                        else:
                            global_vars.lFalseNumberMatches.append(cell.text)
    global_vars.lFalseNumberMatches = list(dict.fromkeys(global_vars.lFalseNumberMatches))


def get_false_words(path):
    # check false word separations
    # get all elements that contain text (p/h1/h2/h3/td)
    # global lAllFalseWordMatches
    lAll = []
    leTextElements = global_vars.tree.xpath('.//*[normalize-space(text())]')
    if os.path.exists(path + '/save_words.pkl'):
        save_file = open(path + '/save_words.pkl', 'rb')
        save_dict = pickle.load(save_file)
        save_file.close()

        for e in leTextElements:
            if e.text:
                for old, new in save_dict.items():
                    e.text = e.text.replace(old, new)
    # print(textElements)
    for e in leTextElements:
        # regex match on every text element to check whether it matches a wrongfully separated word
        # print(e.text)
        if e.text:
            for regex_match in regFalseWords:
                lCurrentMatches = regex_match.findall(e.text)
                if len(lCurrentMatches):
                    lCurrentMatches = [elem for elem in lCurrentMatches if elem not in lAllowedWords]
                    lAll.extend(lCurrentMatches)
    global_vars.lAllFalseWordMatches = list(dict.fromkeys(lAll))


def set_headers():
    # set table headers row for row
    leStandardTables = global_vars.tree.xpath('//table[not(@class="footnote")]')
    for table in leStandardTables:
        fHeader = False
        fBreakOut = False
        iHeaderRows = -1  # -1 for later comparison with 0 index
        iOldHeaderRow = -1
        for row in table:
            for cell in row:
                if cell.text:
                    # first compare cell content to header content matches or date type
                    # if anything matches, set current row to header row
                    if any(list(reg.fullmatch(cell.text) for reg in regHeaderContent)) or is_date(cell.text, False)[0]:
                        fHeader = True
                        iHeaderRows = table.index(row)
                    # then compare to number matches
                    # if it matches here the function quits and reverts back to previous header row
                    if any(list(reg.fullmatch(cell.text) for reg in regNumbers)):
                        # print('found number')
                        iHeaderRows = iOldHeaderRow
                        fBreakOut = True
                        break
            if fBreakOut:
                break
            iOldHeaderRow = iHeaderRows

        # get the first occuring row in which the first cell is not empty
        eFirstTextRow = table.xpath('./tr[td[position() = 1 and text()]][1]')
        if len(eFirstTextRow):
            # index of the first cell with text - 1 to get only empty cells
            iFirstTextCellRow = table.index(eFirstTextRow[0]) - 1
            # compare to header content matches
            if iHeaderRows <= iFirstTextCellRow:
                iHeaderRows = iFirstTextCellRow
                fHeader = True
        # when no header is found and table is of specific size, set first row to header row
        if len(table) >= 4 and get_max_columns(table) >= 3 and iHeaderRows == -1:
            iHeaderRows = 0
            fHeader = True

        if fHeader:
            # create lists with header and body elements
            # this is needed at the beginning, because the position changes when adding header and body tags
            headers = table.xpath('.//tr[position() <= %s]' % str(iHeaderRows + 1))
            body = table.xpath('.//tr[position() > %s]' % str(iHeaderRows + 1))
            # create thead-/tbody-tags
            table.insert(0, etree.Element('tbody'))
            table.insert(0, etree.Element('thead'))

            # move rows to inside header or body
            for thead in headers:
                table.find('thead').append(thead)
            for tbody in body:
                table.find('tbody').append(tbody)


# set all unordered list elements according to regex matches, only for > 1 matches

def set_unordered_list():
    # find and set unordered lists
    leDashCandidates = []
    iDashCount = 0
    for p in global_vars.tree.xpath('//body/p'):
        # check if beginning of paragraph matches safe list denominators
        if p.text:
            # if not check if "- " matches
            if regUnorderedList[0].match(p.text):
                iDashCount += 1
                # append to list for later tag change
                leDashCandidates.append(p)
            else:
                # if only one dash is present, remove last element from dash list (single list item could be confused with
                # wrong break)
                if iDashCount == 1:
                    leDashCandidates.pop()
                iDashCount = 0
    # iterate through dash list and change to unordered list
    for p in leDashCandidates:
        p.text = regUnorderedList[0].sub('', p.text)
        p.tag = 'li'


# remove empty rows

def remove_empty_rows():
    # remove empty table rows
    for row in global_vars.tree.xpath('//tr[* and not(*[node()])]'):
        row.getparent().remove(row)


# this function is very complex because of the nature of tables and cell-merging in html
# it iterates through the columns, therefor indices and range() is used, not the elementwise iteration
# it creates a matrix in which the offsets of all td-cells are documented depending on the colspans within the same
# row, including new colspans from rowspan cells
def split_rowspan():
    # get all tables that have at least one td-attribute of rowspan with a value greater than 1
    rowspanTables = global_vars.tree.xpath('//table[tr/td[@rowspan > 1]]')
    for table in rowspanTables:
        # create 0-matrix of the raw table dimensions
        matrixColspan = [[0 for x in range(get_max_columns(table))] for y in range(len(table))]
        # list to remember already processed cells
        cellHistory = []
        # iterate td
        for i in range(get_max_columns(table)):
            # print('COL: ' + str(i+1))
            # iterate tr
            for j in range(len(table)):
                # print('now cell: ' + str(j + 1) + ' ; ' + str(i + 1 + matrixColspan[j][i]))
                # select cell depending on indices and the offset given by matrix
                cell = table.xpath('./tr[' + str(j + 1) + ']/td[' + str(i + 1 + matrixColspan[j][i]) + ']')
                # if cell was already processed skip to next cell
                if cell in cellHistory:
                    continue
                # if not append it to history
                cellHistory.append(cell)
                # get number of colspan/rowspan if any are present in td tag
                nrCS = cell[0].get('colspan')
                nrRS = cell[0].get('rowspan')
                # print('cell : ' + cell[0].text_content() + ' : has row span: ' + str(nrRS) + ' col span: ' + str(nrCS))
                # if colspan is present, change offset in matrix
                if nrCS is not None and int(nrCS) > 1:
                    # print(matrixColspan)
                    # offset is set, beginning at current cell, starting with 0 and decreasing to negative colspan value + 1
                    for c in range(int(nrCS)):
                        matrixColspan[j][i + c] += -c
                    # for m in range(i + int(nrCS), len(matrixColspan[j])):
                    # change the offset of the remaining cells to maximum negative offset given from colspan value + 1
                    matrixColspan[j][i + int(nrCS):] = [a - int(nrCS) + 1 for a in matrixColspan[j][i + int(nrCS):]]
                    # print(matrixColspan)
                # if cell has rowspan insert corresponding number of empty cells in the following rows
                if nrRS is not None and int(nrRS) > 1:
                    for nrRowspan in range(1, int(nrRS)):
                        # if cell[0].get('colspan') is not None and int(cell[0].get('colspan')) > 1:
                        # if cell has colspan, insert empty cell with equal rowspan attribute
                        if nrCS is not None and int(nrCS) > 1:
                            table[j + nrRowspan].insert(i + matrixColspan[j + nrRowspan][i], etree.Element('td', attrib={'colspan': nrCS}))
                            # print('Inserted new cell in col: ' + str(i + matrixColspan[j + nrRowspan][i]) + ' in row: ' + str(j + nrRowspan))
                        else:
                            table[j + nrRowspan].insert(i + matrixColspan[j + nrRowspan][i], etree.Element('td'))
                            # print('Inserted new cell in col: ' + str(i + matrixColspan[j + nrRowspan][i]) + ' in row: ' + str(j + nrRowspan))
                    # finally remove the rowspan attribute
                    del cell[0].attrib['rowspan']


# merge marked tables vertically
def merge_tables_vertically():
    leMergeTables = global_vars.tree.xpath(
        '//table[tr[1]/td[1][starts-with(normalize-space(text()),"§§")] or tr[last()]/td[last()][starts-with(normalize-space(text()),"§§")]]')
    leToMerge = []
    fContinuedMerge = False
    for table in leMergeTables:
        iCols = []
        fStartMarker = table.xpath('./tr[1]/td[1][starts-with(normalize-space(text()),"§§")]')
        fEndMarker = table.xpath('./tr[last()]/td[last()][starts-with(normalize-space(text()),"§§")]')
        # check if table has end marker (§§)
        if fEndMarker:
            # and start marker?
            if fStartMarker:
                # is merge list empty?
                if not leToMerge:
                    # BUG
                    add_to_errorlog('Error in marker start or end position! Check the markers in ABBYY!\n'
                            'Error found in table with start marker: ' + str(table.xpath('./tr[1]/td[1]/text()')) + '\n'
                            'and end marker: '
                            + str(table.xpath('./tr[last()]/td[last()]/text()')))
                    fContinuedMerge = False
                    global_vars.bFoundError = True
                    continue
                else:
                    leToMerge.append(table)
                    fContinuedMerge = True
            else:
                leToMerge.append(table)
                fContinuedMerge = True
        elif fStartMarker:
            if not leToMerge:
                # BUG
                add_to_errorlog('Error in start marker position! Check the markers in ABBYY!\n'
                      'Error found in table with start marker: ' + str(table.xpath('./tr[1]/td[1]/text()')))
                fContinuedMerge = False
                global_vars.bFoundError = True
                continue
            else:
                leToMerge.append(table)
                fContinuedMerge = False
        else:
            add_to_errorlog('No markers detected, this shouldnt happen, report this bug!')
            global_vars.bFoundError = True
            break
        # next table included in merge?
        # if not merge collected tables
        if not fContinuedMerge:
            # check if all tables in merge list have the same number of columns
            iColNumbers = []
            iTableIndices = []
            for mTable in leToMerge:
                iColNumbers.append(get_max_columns(mTable))
                # get indices of tables to merge
                iTableIndices.append(global_vars.tree.find('body').index(mTable))
            # do all merging candidates have the same number of columns?
            if len(set(iColNumbers)) == 1:
                # before merging, check whether all the tables in this merging process are consecutive tables within
                # the body tag
                # if not only raise warning
                # TODO: raise warning and give user option to not proceed
                if iTableIndices != list(range(min(iTableIndices), max(iTableIndices)+1)):
                    add_to_errorlog('You try to merge tables that are not consecutive within the html.\n'
                          'Please check the table set beginning with'
                          ' ' + str(leToMerge[0].xpath('./tr[last()]/td[last()]/text()')) + ' as end marker, ' +
                          str(len(leToMerge)) + ' subtables and ' +
                          str(iColNumbers) + ' columns.\n\n'
                          'This is fairly unusual, but the merging process will still be executed.\n'
                          'Redo the processing after fixing in ABBYY or Sourcecode, if this was not intentional!')
                    global_vars.bFoundError = True
                # remove end marker
                # for first table
                leToMerge[0].xpath('./tr[last()]/td[last()]')[0].text = leToMerge[0].xpath('./tr[last()]/td[last()]')[
                    0].text.replace('§§', '')
                for i in range(1, len(leToMerge)):
                    # remove start markers
                    if leToMerge[i].xpath('./tr[1]/td[1]')[0].text is not None:
                        leToMerge[i].xpath('./tr[1]/td[1]')[0].text = leToMerge[i].xpath('./tr[1]/td[1]')[
                            0].text.replace('§§', '')
                    # remove end markers
                    # and every other table
                    if leToMerge[i].xpath('./tr[last()]/td[last()]')[0].text is not None:
                        leToMerge[i].xpath('./tr[last()]/td[last()]')[0].text = \
                        leToMerge[i].xpath('./tr[last()]/td[last()]')[0].text.replace('§§', '')
                    # append all rows from all tables to first table
                    for row in leToMerge[i]:
                        leToMerge[0].append(row)
                    # remove now empty table
                    leToMerge[i].getparent().remove(leToMerge[i])
            else:
                add_to_errorlog(
                    'You try to merge tables with different amount of table columns. Fix this in ABBYY or CoCo! Tables will not be merged!')
                add_to_errorlog('Table end marker: ' + str(leToMerge[0].xpath('./tr[last()]/td[last()]/text()')))
                add_to_errorlog('The number of columns within the subtables are: ' + str(iColNumbers))
                global_vars.bFoundError = True
            leToMerge = []


def sup_elements(entry, path):
    with open(path, 'r', encoding='UTF-8') as fi, open('temp.htm', 'w', encoding='UTF-8') as fo:
        rawText = fi.read()
        fi.close()
        os.remove(path)
        lUserSupElements = entry.get().replace(' ', '').split(',')
        for sup in lUserSupElements:
            regexSupMatch = re.compile('(?<!<sup>)' + sup + '(?!</sup>)')
            rawText = regexSupMatch.sub('<sup>' + sup + '</sup>', rawText)
        fo.write(rawText)
        fo.close()
        os.rename('temp.htm', path)
    # leTextNotHeader = tree.xpath('.//*[normalize-space(text()) and not(self::h1] and not(self::h2) and not(self::h3)')


def set_span_headers(lSpanHeaders):
    for span in lSpanHeaders:
        span[0].drop_tag()
        span.tag = 'h3'


def rename_pictures():
    picFolder = os.path.splitext(global_vars.tk.filename)[0] + '_files'
    if os.path.exists(picFolder):
        for filename in os.listdir(picFolder):
            base_file, ext = os.path.splitext(filename)
            if ext == ".png":
                # rename reference in htm file
                # get 'img' tag
                ePngPic = global_vars.tree.xpath('//img[@src="' + os.path.basename(picFolder) + '/' + filename + '"]')
                # rename attribute "src"
                ePngPic[0].attrib['src'] = os.path.basename(picFolder) + '/' + base_file + '.jpg'
                # rename picture file
                os.rename(picFolder + '/' + filename, picFolder + '/' + base_file + ".jpg")


def fix_tsd_separators(decSeparator):
    # exclude header and leftmost column from reformatting
    for table in global_vars.tree.xpath('//table[not(@class="footnote")]'):
        leNumCells = table.xpath('.//tbody/tr/td[position() > 1]')
        for cell in leNumCells:
            if cell.text is not None:
                # only affect cells with numbers
                if re.fullmatch('-?\s?[\d\s,]+', cell.text):
                    # clean all whitespace from number
                    noSpace = cell.text.replace(' ', '')
                    # find nr of decimal places
                    decPlaces = noSpace[::-1].find(',')
                    # if none are found = -1 so fix that to 0
                    if decPlaces < 0 : decPlaces = 0
                    # reformat string to match float format
                    # reformat float to insert thousand separators and preserve the nr of decimal places
                    # replace tsd separators to chosen separator
                    cell.text = '{:,.{prec}f}'.format(float(noSpace.replace(',', '.')), prec=decPlaces).replace(',', ' ').replace('.', decSeparator)


def break_fonds_table():
    eFondsTable = global_vars.tree.xpath(
        '/html/body/*[starts-with(normalize-space(text()),"Vermögensaufstellung")]/following-sibling::table[1]')
    for table in eFondsTable:
        leTitleCells = table.xpath('.//td[position() = 1]')
        leHeaderCells = table.xpath('.//tr[position() <= 2]/td')
        brTags = table.xpath('.//td//br')
        for br in brTags:
            br.tail = ' ' + br.tail
            br.drop_tag()
        for cell in leTitleCells:
            if cell.text:
                lsWrap = text_wrap(cell.text, width=14, break_long_words=False)
                cell.text = lsWrap[0]
                # if len(cell):
                #     print(cell[i].tag)
                for tail in reversed(lsWrap[1:]):
                    brTag = etree.Element('br')
                    brTag.tail = tail
                    cell.insert(0, brTag)
        for cell in leHeaderCells:
            if cell.text:
                lsWrap = text_wrap(cell.text, width=3, break_long_words=False)
                cell.text = lsWrap[0]
                for tail in lsWrap[1:]:
                    brTag = etree.Element('br')
                    brTag.tail = tail
                    cell.append(brTag)


def big_fucking_table():
    secTables = global_vars.tree.xpath('//table[count(tr[1]/td) = 5]')
    for table in secTables:
        for row in table:
            brContent = []
            for cell in row:
                if len(cell):
                    if cell[0].tag == 'br':
                        brContent.append(cell[0].tail)
                        cell.remove(cell[0])
                else:
                    brContent.append(' ')

            if all(elem == ' ' for elem in brContent):
                continue
            if len(brContent) == 5:
                newTr = etree.Element('tr')
                for txt in brContent:
                    newTd = etree.Element('td')
                    newTd.text = txt
                    newTr.append(newTd)
                row.addnext(newTr)

# fSplitRowSpan = BooleanVar(value=1)
# # split rowspan cells
# def split_rowspan():
#     leRowspanTables = tree.xpath('//table[.//td[@rowspan]]')
#     # print(leRowspanTables)
#     eEmptyTd = etree.Element('td')
#     for table in leRowspanTables:
#         for tr in table.xpath('./tr[.//td[@rowspan]]'):
#             print('Row: ' + str(table.index(tr)))
#             for td in tr.xpath('./td[@rowspan]'):
#                 # for iRow in range(int(td.get('rowspan'))):
#                     # table.
#                 print(td)
#                 # td.attrib.pop('rowspan')
#                 table[table.index(tr)+1].insert(tr.index(td), eEmptyTd)
#                 # print('Cell: ' + str(tr.index(td)))
#
#         # for tr in table.xpath('./tr[//td[@rowspan]]'):


# wrap table cells in p tags
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

# first cleaning of the ABBYY htm before the parsing process really starts
def first_cleanse():

    #################
    #  PREPARATIONS #
    #################
    # replace </p><p> in tables with <br>
    # takes the longest, might find better alternative
    for td in global_vars.tree.xpath('//td[count(p)>1]'):
        for p in td.findall('p')[:-1]:
            p.append(etree.Element('br'))

    # change all header hierarchies higher than 3 to 3
    for e in global_vars.tree.xpath('//*[self::h4 or self::h5 or self::h6]'):
        e.tag = 'h3'

    # remove sup/sub tags from headlines
    for e in global_vars.tree.xpath('//*[self::h1 or self::h2 or self::h3]/*[self::sup or self::sub]'):
        e.drop_tag()

    # remove p tags in tables
    for p in global_vars.tree.xpath('//table//p'):
        # print(p.text)
        p.drop_tag()

    # check if report is a fonds report
    if global_vars.tree.xpath('/html/body/*[starts-with(normalize-space(text()),"Vermögensaufstellung")]'):
        global_vars.fIsFondsReport.set(value=1)
        # remove all multiple occurences of dots and ' )'
        # hacky and not that versatile as of now
        for e in global_vars.tree.xpath('.//table//*[text()[not(normalize-space()="")]]'):
            e.text = re.sub('\s*?\.{2,}', '', e.text)
            e.text = re.sub(' \)', ')', e.text)
            e.text = re.sub('\)\s*?\.', ')', e.text)
            if len(e):
                for i in e:
                    if i.tail:
                        i.tail = re.sub('\s*?\.{2,}', '', i.tail)
                        i.tail = re.sub(' \)', ')', i.tail)
                        i.tail = re.sub('\)\s*?\.', ')', i.tail)

    # strip all unnecessary white space
    # nlist = global_vars.tree.xpath('normalize-space(//td)')
    # print(nlist)
    for td in global_vars.tree.xpath('//table//td'):
        if td.text is not None:
            td.text = td.text.strip()
        if td.tail is not None:
            td.tail = td.tail.strip()

    # remove li tags in td elements
    for li in global_vars.tree.xpath('//td/li'):
        li.drop_tag()

    for tag in global_vars.tree.xpath('//*[@class]'):
        # For each element with a class attribute, remove that class attribute
        tag.attrib.pop('class')

    # remove sup/sub tags in unordered list candidates and for non footnote candidates
    for sup in global_vars.tree.xpath('//*[self:: sup or self::sub]'):
        if sup.text is None:
            sup.drop_tag()
        elif any(list(reg.fullmatch(sup.text) for reg in regUnorderedList)):
            sup.drop_tag()
        elif not any(list(reg.fullmatch(sup.text) for reg in regFootnote)) \
                and not any(re.fullmatch(e, sup.text) for e in lSupElements):
            sup.drop_tag()

    # execute only if a formatted html file is used (ABBYY export formatted file)
    if global_vars.tree.xpath('/html/head/style'):
        print('Found formatted File')
        # select all span tags that are the only thing present in a p tag (heading candidates)
        for span in global_vars.tree.xpath('//*[self::span]/ancestor::p'):
            # check if tag contains more than just the span tag
            # if so skip it
            if span.text is None:
                # check if tag contains more than one span tag
                # if so skip it
                if len(span) == 1:
                    global_vars.leSpanHeaders.append(span)

        for br in global_vars.tree.xpath('//br[@*]'):
            br.drop_tag()

    # remove unwanted tags
    cleaner = Cleaner(
        remove_tags=['a', 'head', 'div', 'span'],
        style=True,
        meta=True,
        remove_unknown_tags=False,
        page_structure=False,
        inline_style=True
    )
    tree = cleaner.clean_html(global_vars.tree)
    return tree


####################
# HELPER FUNCTIONS #
####################

# returns TRUE if input string can be interpreted as a date
# if fuzzy is true, ignore unknown tokens in string
def is_date(sInput, bFuzzy):
    try:
        parser.parse(sInput, fuzzy=bFuzzy, parserinfo=GermanParserInfo())
        return [True, False]
    except ValueError:
        try:
            sInput = re.sub('\s', '', sInput)
            parser.parse(sInput, fuzzy=bFuzzy, parserinfo=GermanParserInfo())
            return [True, True]
        except ValueError:
            return [False]


# returns the maximum number of columns in a table as int
def get_max_columns(table):
    # get max number of columns in a row
    firstRow = table.xpath('./tr[1]/td')
    nrCols = 0
    # if there is a colspan in the row, increase by colspan value
    for td in firstRow:
        if td.get('colspan') is not None:
            nrCols += int(td.get('colspan'))
        else:
            nrCols += 1
    return nrCols


# save repl_dict to report folder with name
def save_replacements(repl_dict, name):
    if os.path.exists(global_vars.report_path + name):
        save_file = open(global_vars.report_path + name, 'rb')
        old_dict = pickle.load(save_file)
        repl_dict = {**old_dict, **repl_dict}
        save_file.close()
    save_file = open(global_vars.report_path + name, 'wb')
    pickle.dump(repl_dict, save_file)
    save_file.close()


def add_to_errorlog(text):
    global_vars.lsErrorLog.append(text)
