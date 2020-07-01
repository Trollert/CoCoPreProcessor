import pickle

from lxml import etree
from lxml.html.clean import Cleaner
from textwrap import wrap as text_wrap
import global_vars as gv
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
def replace_word_list(list_new, list_old):
    """
    replace the corrected listbox items with their counterparts
    """
    el_text = gv.tree.xpath('.//*[normalize-space(text())]')
    # get a list of listbox lines
    corrected_list = list(list_new)

    # create duplicate to not create confusion while popping
    list_temp_old = list_old

    # remove unaffected entries from both lists
    for i in reversed(range(len(list_temp_old))):
        if list_temp_old[i] == corrected_list[i]:
            list_temp_old.pop(i)
            corrected_list.pop(i)

    # create file to safe already replaced words in case of error
    save_replacements(dict(zip(list_temp_old, corrected_list)), '/save_words.pkl')

    for e in el_text:
        for i in range(len(corrected_list)):
            if e.text:
                e.text = e.text.replace(list_temp_old[i], corrected_list[i])
            # check tail as well (if present)
            if len(e):
                for t in e:
                    if t.tail:
                        t.tail = t.tail.replace(list_temp_old[i], corrected_list[i])



def replace_number_list(list_new, list_old):
    el_numbers_table = gv.tree.xpath('//table[not(@class="footnote")]/tr/td[normalize-space(text())]')
    # get a list of listbox lines
    list_temp_new = list_new
    list_temp_old = list_old
    for i in reversed(range(len(list_temp_old))):
        if list_temp_old[i] == list_temp_new[i]:
            list_temp_old.pop(i)
            list_temp_new.pop(i)

    # create file to safe already replaced numbers in case of error
    save_replacements(dict(zip(list_temp_old, list_temp_new)), '/save_numbers.pkl')

    for e in el_numbers_table:
        for i in range(len(list_temp_new)):
            if e.text:
                e.text = e.text.replace(list_temp_old[i], list_temp_new[i])


def set_footnote_tables():
    el_tables = gv.tree.xpath('//table')
    # check if tables are footnote tables
    for table in range(len(el_tables)):
        el_first_col_cells = []
        list_b_is_anchor = []
        # check first whether table is exactly 2 columns wide
        if len(el_tables[table].xpath('.//tr[last()]/td')) == 2:
            # create list from first column values
            el_first_col_cells.append(el_tables[table].xpath('.//tr/td[1]'))
            # flatten list
            el_first_col_cells = [item for sublist in el_first_col_cells for item in sublist]
            # check if any footnote regex pattern matches, if yes set corresponding matches list value to true
            for cell in el_first_col_cells:
                # remove sup, sub-tags if found
                for el in cell:
                    if el.tag == 'sup' or el.tag == 'sub':
                        el.drop_tag()
                # create list with bool values of every regex, td-value match
                if cell.text is not None:
                    list_b_is_anchor.append(any(list(reg.fullmatch(cell.text) for reg in regFootnote)))
                else:
                    list_b_is_anchor.append(False)
            # check if all footnote cell values matched with regex pattern
            if all(list_b_is_anchor):
                # if yes set table attribute to "footnote" and insert anchors
                for cell in el_first_col_cells:
                    etree.SubElement(cell, 'a', id='a' + str(table + 1) + str(el_first_col_cells.index(cell)))
                el_tables[table].set('class', 'footnote')

            # clear lists
            el_first_col_cells.clear()
            list_b_is_anchor.clear()


def get_false_numbers(path):
    # check numbers in table cells
    # get all tables that are not footnote tables
    el_standard_tables = gv.tree.xpath('//table[not(@class="footnote")]')
    # if save numbers file exists, replace matches before finding new ones
    if os.path.exists(path + '/save_numbers.pkl'):
        save_file = open(path + '/save_numbers.pkl', 'rb')
        save_dict = pickle.load(save_file)
        save_file.close()
        for table in el_standard_tables:
            for row in table:
                for cell in row:
                    if cell.text is not None:
                        for old, new in save_dict.items():
                            cell.text = cell.text.replace(old, new)

    for table in el_standard_tables:
        el_subtables = []
        i_format_count = [0] * (len(regNumbers) + 1)
        # select all non-empty td-elements, beginning at second column
        el_subtables.append(table.xpath('.//tr/td[position() > 1 and normalize-space(text())]'))
        for row in el_subtables:
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
                    cell_without_br = ''
                    if cell.find('br') is not None:
                        all_br = cell.findall('br')
                        cell_without_br = cell.text
                        for br in all_br:
                            cell_without_br += ' ' + br.tail
                    if cell_without_br:
                        cell_without_br = re.sub(r'(\t|\n)', '', cell_without_br)

                    # if any format matched increase the table counter and dont change anything
                    if sum(cell_format):
                        i_format_count = [a + b for a, b in zip(i_format_count, cell_format)]
                    # if br-tags where present within the cell, check that first
                    elif cell_without_br and is_date(cell_without_br, False)[0]:
                        i_format_count[-1] += 1
                    # if not check normally
                    elif is_date(cell.text, False)[0]:
                        i_format_count[-1] += 1
                        if is_date(cell.text, False)[1]:
                            cell.text = re.sub('\s', '', cell.text)
                    elif any(reg.fullmatch(cell.text) for reg in regMisc + regHeaderContent):
                        continue
                    # if no match could be found, try to fix it or move it to false match list
                    else:
                        if gv.b_fix_numbers.get():
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
                                    gv.list_false_number_matches.append(cell.text)
                            # otherwise append it to false number match list
                            else:
                                gv.list_false_number_matches.append(cell.text)
                        else:
                            gv.list_false_number_matches.append(cell.text)
    gv.list_false_number_matches = list(dict.fromkeys(gv.list_false_number_matches))


def get_false_words(path):
    # check false word separations
    # get all elements that contain text (p/h1/h2/h3/td)
    # global lAllFalseWordMatches
    list_all_matches = []
    el_all_text = gv.tree.xpath('.//*[normalize-space(text())]')
    # check for saved replacements and apply them if found
    if os.path.exists(path + '/save_words.pkl'):
        save_file = open(path + '/save_words.pkl', 'rb')
        save_dict = pickle.load(save_file)
        save_file.close()
        for e in el_all_text:
            if e.text:
                for old, new in save_dict.items():
                    e.text = e.text.replace(old, new)
                    # check tail as well
                    if len(e):
                        for t in e:
                            if t.tail:
                                t.tail = t.tail.replace(old, new)
    # regex match on every text element to check whether it matches a wrongfully separated word
    for e in el_all_text:
        if e.text:
            for regex_match in regFalseWords:
                list_current_matches = regex_match.findall(e.text_content())
                if len(list_current_matches):
                    list_current_matches = [elem for elem in list_current_matches if elem not in lAllowedWords]
                    list_all_matches.extend(list_current_matches)
    gv.list_false_word_matches = list(dict.fromkeys(list_all_matches))


def remove_false_text_breaks():
    """
    this function merges p-elements depending on line-end and line-start characters
    this is basically just for removing falsely separated paragraphs
    """
    all_text_elements = gv.tree.xpath('/html/body/p')
    if gv.flag_is_formatted:
        for i in range(len(all_text_elements)):
            try:
                # check end and start char of two adjacent p-tag-strings
                if reg_false_break_indicator_end.search(all_text_elements[i].text_content()) and \
                        reg_false_break_indicator_start.search(all_text_elements[i+1].text_content()):
                    # add space if needed
                    if not all_text_elements[i].text_content().endswith(' '):
                        all_text_elements[i+1][0].text = ' ' + all_text_elements[i+1][0].text
                    # append second element to first
                    all_text_elements[i].append(all_text_elements[i+1])
                    # remove the tag from second element to prevent nested paragraphs
                    all_text_elements[i+1].drop_tag()
            except IndexError:
                # this exception is only raised when reaching the end of the list
                # so this is just ignored
                continue
    else:
        for i in range(len(all_text_elements)):
            try:
                # check end and start char of two adjacent p-tag-strings
                if reg_false_break_indicator_end.search(all_text_elements[i].text_content()) and \
                        reg_false_break_indicator_start.search(all_text_elements[i+1].text_content()):
                    # add space if needed
                    if not all_text_elements[i].text_content().endswith(' '):
                        all_text_elements[i+1].text = ' ' + all_text_elements[i+1].text
                    # append second element to first
                    all_text_elements[i].append(all_text_elements[i+1])
                    # remove the tag from second element to prevent nested paragraphs
                    all_text_elements[i+1].drop_tag()
            except IndexError:
                # this exception is only raised when reaching the end of the list
                # so this is just ignored
                continue


def set_headers():
    # set table headers row for row
    el_standard_tables = gv.tree.xpath('//table[not(@class="footnote")]')
    for table in el_standard_tables:
        flag_is_header = False
        flag_break_out = False
        i_header_rows = -1  # -1 for later comparison with 0 index
        i_old_header_row = -1
        for row in table:
            for cell in row:
                if cell.text:
                    # first compare cell content to header content matches or date type
                    # if anything matches, set current row to header row
                    if any(list(reg.fullmatch(cell.text) for reg in regHeaderContent)) or is_date(cell.text, False)[0]:
                        flag_is_header = True
                        i_header_rows = table.index(row)
                    # then compare to number matches
                    # if it matches here the function quits and reverts back to previous header row
                    if any(list(reg.fullmatch(cell.text) for reg in regNumbers)):
                        # print('found number')
                        i_header_rows = i_old_header_row
                        flag_break_out = True
                        break
            if flag_break_out:
                break
            i_old_header_row = i_header_rows

        # get the first occuring row in which the first cell is not empty
        el_first_non_empty_row = table.xpath('./tr[td[position() = 1 and text()]][1]')
        if len(el_first_non_empty_row):
            # index of the first cell with text - 1 to get only empty cells
            first_text_cell_row = table.index(el_first_non_empty_row[0]) - 1
            # compare to header content matches
            if i_header_rows <= first_text_cell_row:
                i_header_rows = first_text_cell_row
                flag_is_header = True
        # when no header is found and table is of specific size, set first row to header row
        if len(table) >= 4 and get_max_columns(table) >= 3 and i_header_rows == -1:
            i_header_rows = 0
            flag_is_header = True
        # if the whole table would be headers just set the first one to header
        if len(table) == i_header_rows + 1:
            i_header_rows = 0

        if flag_is_header:
            # create lists with header and body elements
            # this is needed at the beginning, because the position changes when adding header and body tags
            headers = table.xpath('.//tr[position() <= %s]' % str(i_header_rows + 1))
            body = table.xpath('.//tr[position() > %s]' % str(i_header_rows + 1))
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
    list_dash_candidates = []
    i_dash_count = 0
    flag_end_block = False
    current_block_dash = ''
    index_indent = []
    for p in gv.tree.xpath('//body/p'):
        # check if beginning of paragraph matches safe list denominators
        if p.text:
            # create match object,
            # None if nothing was matched
            # returns match when something was found
            object_match = regUnorderedList[0].match(p.text)
            if object_match:
                # if this is the first element in this chunk define dash denominator
                if not i_dash_count:
                    current_block_dash = object_match.group(0)
                i_dash_count += 1
                # check if the next element in root is also p
                if p.getnext().tag == 'p':
                    # if current dash denominator is not equal to the first dash
                    # this might be a indented list element so append its index to list
                    if current_block_dash != object_match.group(0):
                        index_indent.append(i_dash_count - 1)
                    list_dash_candidates.append(p)
                # if only one dashed element was found, check if it ends with a dot and only append if it did
                elif i_dash_count == 1:
                    flag_end_block = True
                    if p.text.endswith('.'):
                        list_dash_candidates.append(p)
                # if next element is not of type p, check if current dash is of chunk type,
                # if not check whether it might be of an indented group
                elif current_block_dash != object_match.group(0):
                    flag_end_block = True
                    if object_match.group(0) == list_dash_candidates[-1].text[:2]:
                        list_dash_candidates.append(p)
                        index_indent.append(i_dash_count - 1)
                else:
                    flag_end_block = True
                    list_dash_candidates.append(p)
            # if dash elements were found, but its only one and it doesnt end with a dot, pop it from candidate list
            elif list_dash_candidates:
                flag_end_block = True
                if i_dash_count == 1 and not list_dash_candidates[0].text.endswith('.'):
                    list_dash_candidates.pop()
        # if flag_end_block is True, convert the current block to li
        if flag_end_block:
            flag_end_block = False
            # only execute if dash elements were found
            if list_dash_candidates:
                # select parent body-tag
                currentParent = list_dash_candidates[0].getparent()
                # insert outer ul-tag at the index of the first dash group element
                outerUl = etree.Element('ul')
                currentParent.insert(currentParent.index(list_dash_candidates[0]), outerUl)
                # change tag of all dash elements to li and insert into ul-tag
                for li in list_dash_candidates:
                    li.text = regUnorderedList[0].sub('', li.text, count=1)
                    li.tag = 'li'
                    outerUl.append(li)
                # if indented elements were found, split index-list into sublists of consecutive chunks
                if index_indent and gv.b_indent_unordered_list.get():
                    # iterate in reverse order to not mess up already moved elements
                    for subList in reversed(split_non_consecutive(index_indent)):
                        # insert inner ul-tag at first sublist elements position
                        innerUl = etree.Element('ul')
                        outerUl.insert(subList[0], innerUl)
                        # finally move indented elements into the ul-tag
                        for elem in subList:
                            innerUl.append(list_dash_candidates[elem])
                list_dash_candidates.clear()
                index_indent.clear()
            i_dash_count = 0


# remove empty rows
def remove_empty_rows():
    # remove empty table rows
    for row in gv.tree.xpath('//tr[* and not(*[node()])]'):
        row.getparent().remove(row)


# this function is very complex because of the nature of tables and cell-merging in html
# it iterates through the columns, therefor indices and range() is used, not the element-wise iteration
# it creates a matrix in which the offsets of all td-cells are documented depending on the colspans within the same
# row, including new colspans from rowspan cells
def split_rowspan():
    # get all tables that have at least one td-attribute of rowspan with a value greater than 1
    el_rowspan_tables = gv.tree.xpath('//table[tr/td[@rowspan > 1]]')
    for table in el_rowspan_tables:
        # create 0-matrix of the raw table dimensions
        matrix_correction = [[0 for x in range(get_max_columns(table))] for y in range(len(table))]
        # list to remember already processed cells
        cell_history = []
        # iterate td
        for i in range(get_max_columns(table)):
            # print('COL: ' + str(i+1))
            # iterate tr
            for j in range(len(table)):
                # print('now cell: ' + str(j + 1) + ' ; ' + str(i + 1 + matrix_correction[j][i]))
                # select cell depending on indices and the offset given by matrix
                cell = table.xpath('./tr[' + str(j + 1) + ']/td[' + str(i + 1 + matrix_correction[j][i]) + ']')
                # if cell was already processed skip to next cell
                if cell in cell_history:
                    continue
                # if not append it to history
                cell_history.append(cell)
                # get number of colspan/rowspan if any are present in td tag
                nr_cs = cell[0].get('colspan')
                nr_rs = cell[0].get('rowspan')
                # print('cell : ' + cell[0].text_content() + ' : has row span: ' + str(nr_rs) + ' col span: ' + str(nr_cs))
                # if colspan is present, change offset in matrix
                if nr_cs is not None and int(nr_cs) > 1:
                    # print(matrix_correction)
                    # offset is set, beginning at current cell, starting with 0 and decreasing to negative colspan value + 1
                    for c in range(int(nr_cs)):
                        matrix_correction[j][i + c] += -c
                    # for m in range(i + int(nr_cs), len(matrix_correction[j])):
                    # change the offset of the remaining cells to maximum negative offset given from colspan value + 1
                    matrix_correction[j][i + int(nr_cs):] = [a - int(nr_cs) + 1 for a in matrix_correction[j][i + int(nr_cs):]]
                    # print(matrix_correction)
                # if cell has rowspan insert corresponding number of empty cells in the following rows
                if nr_rs is not None and int(nr_rs) > 1:
                    for nrRowspan in range(1, int(nr_rs)):
                        # if cell[0].get('colspan') is not None and int(cell[0].get('colspan')) > 1:
                        # if cell has colspan, insert empty cell with equal rowspan attribute
                        if nr_cs is not None and int(nr_cs) > 1:
                            table[j + nrRowspan].insert(i + matrix_correction[j + nrRowspan][i], etree.Element('td', attrib={'colspan': nr_cs}))
                            # print('Inserted new cell in col: ' + str(i + matrix_correction[j + nrRowspan][i]) + ' in row: ' + str(j + nrRowspan))
                        else:
                            table[j + nrRowspan].insert(i + matrix_correction[j + nrRowspan][i], etree.Element('td'))
                            # print('Inserted new cell in col: ' + str(i + matrix_correction[j + nrRowspan][i]) + ' in row: ' + str(j + nrRowspan))
                    # finally remove the rowspan attribute
                    del cell[0].attrib['rowspan']


# merge marked tables vertically
def merge_tables_vertically():
    el_merge_tables = gv.tree.xpath(
        '//table[tr[1]/td[1][starts-with(normalize-space(text()),"§§")] or tr[last()]/td[last()][starts-with(normalize-space(text()),"§§")]]')
    list_to_merge = []
    flag_continue_merge = False
    for table in el_merge_tables:
        iCols = []
        flag_start_marker = table.xpath('./tr[1]/td[1][starts-with(normalize-space(text()),"§§")]')
        flag_end_marker = table.xpath('./tr[last()]/td[last()][starts-with(normalize-space(text()),"§§")]')
        # check if table has end marker (§§)
        if flag_end_marker:
            # and start marker?
            if flag_start_marker:
                # is merge list empty?
                if not list_to_merge:
                    # BUG
                    add_to_error_log('Error in marker start or end position! Check the markers in ABBYY!\n'
                            'Error found in table with start marker: ' + str(table.xpath('./tr[1]/td[1]/text()')) + '\n'
                            'and end marker: '
                                     + str(table.xpath('./tr[last()]/td[last()]/text()')))
                    flag_continue_merge = False
                    gv.flag_found_error = True
                    continue
                else:
                    list_to_merge.append(table)
                    flag_continue_merge = True
            else:
                list_to_merge.append(table)
                flag_continue_merge = True
        elif flag_start_marker:
            if not list_to_merge:
                # BUG
                add_to_error_log('Error in start marker position! Check the markers in ABBYY!\n'
                      'Error found in table with start marker: ' + str(table.xpath('./tr[1]/td[1]/text()')))
                flag_continue_merge = False
                gv.flag_found_error = True
                continue
            else:
                list_to_merge.append(table)
                flag_continue_merge = False
        else:
            add_to_error_log('No markers detected, this shouldnt happen, report this bug!')
            gv.flag_found_error = True
            break
        # next table included in merge?
        # if not merge collected tables
        if not flag_continue_merge:
            # check if all tables in merge list have the same number of columns
            i_col_numbers = []
            index_tables = []
            for mTable in list_to_merge:
                i_col_numbers.append(get_max_columns(mTable))
                # get indices of tables to merge
                index_tables.append(gv.tree.find('body').index(mTable))
            # do all merging candidates have the same number of columns?
            if len(set(i_col_numbers)) == 1:
                # before merging, check whether all the tables in this merging process are consecutive tables within
                # the body tag
                # if not only raise warning
                # TODO: raise warning and give user option to not proceed
                if index_tables != list(range(min(index_tables), max(index_tables)+1)):
                    add_to_error_log('You try to merge tables that are not consecutive within the html.\n'
                          'Please check the table set beginning with'
                          ' ' + str(list_to_merge[0].xpath('./tr[last()]/td[last()]/text()')) + ' as end marker, ' +
                                     str(len(list_to_merge)) + ' subtables and ' +
                                     str(i_col_numbers) + ' columns.\n\n'
                          'This is fairly unusual, but the merging process will still be executed.\n'
                          'Redo the processing after fixing in ABBYY or Sourcecode, if this was not intentional!')
                    gv.flag_found_error = True
                # remove end marker
                # for first table
                list_to_merge[0].xpath('./tr[last()]/td[last()]')[0].text = list_to_merge[0].xpath('./tr[last()]/td[last()]')[
                    0].text.replace('§§', '')
                for i in range(1, len(list_to_merge)):
                    # remove start markers
                    if list_to_merge[i].xpath('./tr[1]/td[1]')[0].text is not None:
                        list_to_merge[i].xpath('./tr[1]/td[1]')[0].text = list_to_merge[i].xpath('./tr[1]/td[1]')[
                            0].text.replace('§§', '')
                    # remove end markers
                    # and every other table
                    if list_to_merge[i].xpath('./tr[last()]/td[last()]')[0].text is not None:
                        list_to_merge[i].xpath('./tr[last()]/td[last()]')[0].text = \
                            list_to_merge[i].xpath('./tr[last()]/td[last()]')[0].text.replace('§§', '')
                    # append all rows from all tables to first table
                    for row in list_to_merge[i]:
                        list_to_merge[0].append(row)
                    # remove now empty table
                    list_to_merge[i].getparent().remove(list_to_merge[i])
            else:
                add_to_error_log(
                    'You try to merge tables with different amount of table columns. Fix this in ABBYY or CoCo! Tables will not be merged!')
                add_to_error_log('Table end marker: ' + str(list_to_merge[0].xpath('./tr[last()]/td[last()]/text()')))
                add_to_error_log('The number of columns within the subtables are: ' + str(i_col_numbers))
                gv.flag_found_error = True
            list_to_merge = []


def sup_elements(entry, path):
    with open(path, 'r', encoding='UTF-8') as fi, open('temp.htm', 'w', encoding='UTF-8') as fo:
        raw_text = fi.read()
        fi.close()
        os.remove(path)
        list_user_input = entry.get().replace(' ', '').split(',')
        for sup in list_user_input:
            regexSupMatch = re.compile('(?<!<sup>)' + sup + '(?!</sup>)')
            raw_text = regexSupMatch.sub('<sup>' + sup + '</sup>', raw_text)
        fo.write(raw_text)
        fo.close()
        os.rename('temp.htm', path)
    # leTextNotHeader = tree.xpath('.//*[normalize-space(text()) and not(self::h1] and not(self::h2) and not(self::h3)')


class SpanFont:
    def __init__(self, name):
        self.name = name
        self.font_sizes = {}
        self.font_occurrences = {}

    def add_font(self, identifier, size):
        self.font_sizes[identifier] = size
        self.font_occurrences[identifier] = 0

    def add_occurrence(self, identifier, occurrence=1):
        self.font_occurrences[identifier] += occurrence

    def get_max_key(self):
        return max(self.font_occurrences, key=self.font_occurrences.get)


def analyze_style_tag(style_element, p_elements, accuracy=10):
    # get list of raw style font text
    print(style_element[0].text.splitlines())
    list_styles = [element for element in style_element[0].text.splitlines() if element.startswith(' .font')]
    print(list_styles)
    # extract font sizes as integer list
    list_font_sizes = [int(re.findall(r'(?<=font:)\d+(?=pt)', size)[0]) for size in list_styles]
    # extract font name as string list
    list_font_names = [re.findall(r'(?<=pt )[\w\s]*?(?=,)', style)[0] for style in list_styles]
    # create list of font identifiers ('font0, font1, ...)
    list_font_identifiers = ['font' + str(i) for i in range(len(list_styles))]
    # create dict from identifiers and sizes
    font_sizes = dict(zip(list_font_identifiers, list_font_sizes))
    # create dict from identifiers and names
    font_names = dict(zip(list_font_identifiers, list_font_names))

    # create dict for occurrence count
    font_occurrences = dict(zip(list_font_identifiers, [0] * len(list_styles)))
    print(font_occurrences)
    # count all the occurrences of the specific fonts
    for p in p_elements:
        font_occurrences[re.findall(r'font\d+', p.find('span').attrib['class'])[0]] += 1
    # get percentages of occurrences
    sum_occurrences = sum(font_occurrences.values())
    font_occurrence_percentage = dict(zip(list_font_identifiers, [k / sum_occurrences for k in font_occurrences.values()]))
    print(font_occurrence_percentage)
    # pop zero element candidates from all lists
    poplist = []
    for key, value in font_occurrences.items():
        if value == 0:
            poplist.append(key)
    for key in poplist:
        font_occurrences.pop(key)
        font_sizes.pop(key)
        font_occurrence_percentage.pop(key)

    # mark all possible heading candidates
    max_key = max(font_occurrence_percentage, key=font_occurrence_percentage.get)
    print(max_key)
    max_value = font_occurrence_percentage[max_key]
    max_size = font_sizes[max_key]
    heading_candidates = {}
    for key, value in font_occurrence_percentage.items():
        if max_value > value + (accuracy / 100) and font_sizes[key] >= max_size + accuracy / 5:
            if font_names[key] == font_names[max_key]:
                heading_candidates[key] = 1
            elif font_sizes[key] > max_size + accuracy / 4:
                heading_candidates[key] = 1

    print(heading_candidates)
    return heading_candidates


def set_span_headers():
    for p in gv.tree.xpath('/html/body/p[count(*)>1]/span[@style or @class]/parent::*'):
        span = p.findall('span')
        class_attrib = int(re.findall(r'(?<=font)\d+', span[0].attrib['class'])[0])
        for s in span[1:]:
            if hasattr(s, 'class'):
                fontsize = int(re.findall(r'(?<=font)\d+', s.attrib['class'])[0])
                if fontsize > class_attrib:
                    class_attrib = fontsize
            span[0].append(s)
            s.drop_tag()
        span[0].attrib['class'] = 'font' + str(class_attrib)

    # select all span tags that are the only thing present in a p tag (heading candidates)
    for p in gv.tree.xpath('/html/body/p[count(*)=1]/span[@style]/parent::*'):
        try:
            if p[0].attrib['style'] in ['font-weight:bold;', 'font-style:italic;', 'text-decoration:underline;']:
                if not p.xpath('./span[normalize-space(.)]')[0].text.endswith(('.', ':')):
                    p.tag = 'h3'
        except KeyError:
            pass

    style_content = gv.tree.xpath('/html/head/style')
    el_spans = gv.tree.xpath('body/p[count(*)=1 and not(text())]/span[@class]/parent::*')

    heading_candidates = analyze_style_tag(style_content, el_spans, 10)

    for p in el_spans:
        if re.findall(r'font\d+', p[0].attrib['class'])[0] in heading_candidates \
                and not p[0].text.endswith(('.', ':')) \
                and not regUnorderedList[0].match(p[0].text) \
                and not regUnorderedList[0].match(p.getnext().text_content()):
            p.tag = 'h3'
    for br in gv.tree.xpath('//br[@*]'):
        br.drop_tag()

    # get style tag content at the start of the document

    # convert it to list with only font classes
    # list_styles = [element for element in style_content[0].text.splitlines() if element.startswith(' .font')]
    # # extract the font class indices
    # list_font_sizes = [int(re.findall(r'(?<=font:)\d+(?=pt)', size)[0]) for size in list_styles]
    # font_sizes = dict(zip(['font' + str(i) for i in range(len(list_styles))], list_font_sizes))
    # # get all p elements with span child with 'class' attribute that are children of p and are an only child and dont contain text
    #
    # # create dict with font names and 0 values
    # font_occurrences = dict(zip(['font' + str(i) for i in range(len(list_styles))], [0] * len(list_styles)))
    # # fill occurrence dict, to determine which font size is associated with normal text
    # for p in el_spans:
    #     # increase index of font class in occList by one for each span element
    #     font_occurrences[re.findall(r'font\d+', p.find('span').attrib['class'])[0]] += 1
    # # get the key of the maximum number of occurring font text
    # max_key_font = max(font_occurrences, key=font_occurrences.get)
    # # get the percentage of occurrence of each font style
    # sum_occurrences = sum(font_occurrences.values())
    # percentage_occurrence = dict(zip(font_occurrences.keys(), [k / sum_occurrences for k in font_occurrences.values()]))
    # for key, value in percentage_occurrence.items():
    #     if value == 0:
    #         font_occurrences.pop(key)
    # print(f'Percentages: {percentage_occurrence}')
    #
    # list_fonts_size = []
    # for style in list_styles:
    #     font_name = re.findall(r'(?<=pt )[\w\s]*?(?=,)', style)[0]
    #     font_size = int(re.findall(r'(?<=font:)\d+(?=pt)', style)[0])
    #     if not list_fonts_size:
    #         list_fonts_size.append([font_size, font_name])
    #     elif font_name != list_fonts_size[-1][-1] and font_size != list_fonts_size[-1][-2]:
    #         list_fonts_size.append([font_size, font_name])
    #     elif font_name == list_fonts_size[-1][-1] and font_size != list_fonts_size[-1][-2]:
    #         list_fonts_size[-1].insert(-1, font_size)
    #
    # # print(f'List font size: {list_fonts_size}')
    # main_font = max(list_fonts_size, key=len)[-1]
    # index_main_font = max((len(l), i) for i, l in enumerate(list_fonts_size))[1]
    # # print(main_font)
    # # print(index_main_font)
    # #
    # # print(f'Font list: {list_font_sizes}')
    # list_font_sizes = [int(re.findall(r'(?<=font:)\d+(?=pt)', size)[0]) for size in list_styles]
    # # cut list when value of font size is no longer increasing (indicates font style change)
    # list_filtered_fonts = [list_font_sizes[0]]
    # for i in range(1, len(list_font_sizes)):
    #     if list_font_sizes[i] >= list_font_sizes[i-1]:
    #         list_filtered_fonts.append(list_font_sizes[i])
    #     else:
    #         break
    #
    # # print(f'List of fontsizes: {list_occurrences}')
    # print(f'Index of max: {max_key_font}')



def rename_pictures():
    folder_pics = os.path.splitext(gv.tk.filename)[0] + '_files'
    if os.path.exists(folder_pics):
        for filename in os.listdir(folder_pics):
            base_file, ext = os.path.splitext(filename)
            if ext == ".png":
                # rename reference in htm file
                # get 'img' tag
                e_png_pic = gv.tree.xpath('//img[@src="' + os.path.basename(folder_pics) + '/' + filename + '"]')
                # rename attribute "src"
                e_png_pic[0].attrib['src'] = os.path.basename(folder_pics) + '/' + base_file + '.jpg'
                # rename picture file
                os.rename(folder_pics + '/' + filename, folder_pics + '/' + base_file + ".jpg")


# this function fixed falsly formatted numbers within tables which should be thousand-separated by a space and decimal
# separated by a chooseable separator "decSeparator"
# the precision of decimal places is adopted from each original number
def fix_tsd_separators(dec_separator):
    # exclude header and leftmost column from reformatting
    for table in gv.tree.xpath('//table[not(@class="footnote")]'):
        for cell in table.xpath('.//tbody/tr/td[position() > 1]'):
            if cell.text is not None:
                # only affect cells with numbers
                if re.fullmatch('-?\s?[\d\s,]+', cell.text):
                    # clean all whitespace from number
                    no_space = cell.text.replace(' ', '')
                    # find nr of decimal places
                    nr_dec_places = no_space[::-1].find(dec_separator)
                    # if none are found = -1 so fix that to 0
                    if nr_dec_places < 0 : nr_dec_places = 0
                    # reformat string to match float format
                    # reformat float to insert thousand separators and preserve the nr of decimal places
                    # replace tsd separators to chosen separator
                    cell.text = '{:,.{prec}f}'.format(float(no_space.replace(',', '.')), prec=nr_dec_places).replace(',', ' ').replace('.', dec_separator)


# this function inserts br-tags in the header and first column of the big "Vermögensaufstellung" Table in fonds reports
# it hereby wraps the cell text to a specific length, which is set to 14 characters while not breaking longer words
def break_fonds_table():
    e_fonds_table = gv.tree.xpath(
        '/html/body/*[starts-with(normalize-space(text()),"Vermögensaufstellung")]/following-sibling::table[1]')
    for table in e_fonds_table:
        title_col_cells = table.xpath('.//td[position() = 1]')
        header_cells = table.xpath('.//tr[position() <= 2]/td')
        # remove br-tags in this table
        br_tags = table.xpath('.//td//br')
        for br in br_tags:
            # insert space before tail text
            br.tail = ' ' + br.tail
            br.drop_tag()
        # iterate leftmost column
        for cell in title_col_cells:
            if cell.text:
                # wrap text into sizeable chunks of max 14 chars
                list_wrap = text_wrap(cell.text, width=14, break_long_words=False)
                # set first chunk to cell text
                cell.text = list_wrap[0]
                # append rest as br-tail
                for tail in reversed(list_wrap[1:]):
                    br_tag = etree.Element('br')
                    br_tag.tail = tail
                    cell.insert(0, br_tag)
        for cell in header_cells:
            if cell.text:
                list_wrap = text_wrap(cell.text, width=3, break_long_words=False)
                cell.text = list_wrap[0]
                for tail in list_wrap[1:]:
                    br_tag = etree.Element('br')
                    br_tag.tail = tail
                    cell.append(br_tag)


def big_fucking_table():
    secTables = gv.tree.xpath('//table[count(tr[6]/td) = 33]')
    for row in secTables[0][2:]:
        brContent = []
        for cell in row[-5:]:
            if len(cell) == 1:
                if cell[0].tag == 'br':
                    brContent.append(cell[0].tail)
                    cell.remove(cell[0])
            else:
                brContent.append(' ')

        if all(elem == ' ' for elem in brContent):
            continue
        if len(brContent) == 5:
            newTr = etree.Element('tr')
            for i in range(28):
                newTr.append(etree.Element('td'))
            for txt in brContent:
                newTd = etree.Element('td')
                newTd.text = txt
                newTr.append(newTd)
            row.addnext(newTr)


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


def clean_whitespace(element):
    # remove all repeating and trailing whitespace
    for e in element.iter():
        if e.text:
            e.text = re.sub(r'( |&nbsp;|\t){2,}', ' ', e.text)
            # e.text = e.text.strip()
        if e.tail:
            e.tail = re.sub(r'\s{2,}', ' ', e.tail)
            # e.tail = e.tail.strip()


# first cleaning of the ABBYY htm before the parsing process really starts
def pre_cleanup():
    #################
    #  PREPARATIONS #
    #################
    # replace </p><p> in tables with <br>
    for td in gv.tree.xpath('//td[count(p)>1]'):
        for p in td.findall('p')[:-1]:
            p.append(etree.Element('br'))

    clean_whitespace(gv.tree)

    # remove p tags in tables
    for p in gv.tree.xpath('//table//p | //table//span'):
        # print(p.text)
        p.drop_tag()

    # change all header hierarchies higher than 3 to 3
    for e in gv.tree.xpath('//*[self::h4 or self::h5 or self::h6]'):
        e.tag = 'h3'

    # remove sup/sub tags from headlines
    for e in gv.tree.xpath('//*[self::h1 or self::h2 or self::h3]/*[self::sup or self::sub]'):
        e.drop_tag()

    # check if report is a fonds report
    if gv.tree.xpath('/html/body/*[starts-with(normalize-space(text()),"Vermögensaufstellung")]'):
        gv.b_fonds_report.set(value=1)
        # remove all multiple occurences of dots and ' )'
        # hacky and not that versatile as of now
        for e in gv.tree.xpath('.//table//*[text()[not(normalize-space()="")]]'):
            if e.text:
                e.text = re.sub('\s*?\.{2,}', '', e.text)
                e.text = re.sub(' \)', ')', e.text)
                e.text = re.sub('\)\s*?\.', ')', e.text)
                if len(e):
                    for i in e:
                        if i.tail:
                            i.tail = re.sub('\s*?\.{2,}', '', i.tail)
                            i.tail = re.sub(' \)', ')', i.tail)
                            i.tail = re.sub('\)\s*?\.', ')', i.tail)



    # remove li tags in td elements
    for li in gv.tree.xpath('//td/li'):
        li.drop_tag()

    # check if .htm-file is formatted and proceed accordingly
    # execute only if a formatted html file is used (ABBYY export formatted file)
    if gv.tree.xpath('//span'):
        gv.flag_is_formatted = True
        gv.b_span_headings.set(value=1)
        cleaner = Cleaner(
            remove_tags=['a', 'div'],
            style=False,
            meta=False,
            remove_unknown_tags=False,
            page_structure=False,
            inline_style=False,
            safe_attrs_only=False
        )
        gv.tree = cleaner.clean_html(gv.tree)
        print('Found formatted File')
    else:
        cleaner = Cleaner(
            remove_tags=['a', 'head', 'div', 'span'],
            style=True,
            meta=True,
            remove_unknown_tags=False,
            page_structure=False,
            inline_style=True
        )
        gv.tree = cleaner.clean_html(gv.tree)

    # remove sup/sub tags in unordered list candidates and for non footnote candidates
    for sup in gv.tree.xpath('//*[self:: sup or self::sub]'):
        if sup.text is None:
            sup.drop_tag()
        elif any(list(reg.fullmatch(sup.text) for reg in regUnorderedList)):
            sup.drop_tag()
        elif not any(list(reg.fullmatch(sup.text) for reg in regFootnote)) \
                and not any(re.fullmatch(e, sup.text) for e in lSupElements):
            sup.drop_tag()

    return gv.tree


# cleanup after generating
def post_cleanup(user_input):
    # wrap all table contents in p-tags
    # wrap(tree, "p")

    # clean brbr tags
    for h in gv.tree.xpath('//*[self::h1 or self::h2 or self::h3]/br/parent::*'):
        print(h)
        br = h.findall('br')
        if len(br):
            for i in range(len(br)):
                if not br[i].tail and br[i+1].tail:
                    sibling = etree.Element(h.tag)
                    sibling.insert(0, br[i+1])
                    h.addnext(sibling)
                    br[i].drop_tag()
                    br[i+1].drop_tag()
                    i += 1

    # write to new file in source folder
    print(os.path.splitext(gv.tk.filename)[0])
    gv.tree.write(os.path.splitext(gv.tk.filename)[0] + '_modified.htm', encoding='UTF-8', method='html')
    if gv.b_sup_elements.get():
        sup_elements(user_input, os.path.splitext(gv.tk.filename)[0] + '_modified.htm')

    # clean up user_words.txt
    f = open(gv.path_root_UI + '/user_words.txt', 'r', encoding='utf-8')
    l = f.read().splitlines()
    f.close()
    f = open(gv.path_root_UI + '/user_words.txt', 'w', encoding='utf-8')

    f.write('\n'.join(list(dict.fromkeys(l))) + '\n')
    f.close()


def span_cleanup():
    if gv.flag_is_formatted:
        cleaner = Cleaner(
            remove_tags=['span', 'head'],
            style=True,
            meta=True,
            remove_unknown_tags=False,
            page_structure=False,
            inline_style=True
        )
        gv.tree = cleaner.clean_html(gv.tree)

####################
# HELPER FUNCTIONS #
####################


# returns TRUE if input string can be interpreted as a date
# if fuzzy is true, ignore unknown tokens in string
def is_date(date_input, flag_fuzzy):
    try:
        parser.parse(date_input, fuzzy=flag_fuzzy, parserinfo=GermanParserInfo())
        return [True, False]
    except ValueError:
        try:
            date_input = re.sub('\s', '', date_input)
            parser.parse(date_input, fuzzy=flag_fuzzy, parserinfo=GermanParserInfo())
            return [True, True]
        # todo: clear up exceptions
        except:
            return [False]
    except:
        return [False]


# returns the maximum number of columns in a table as int
def get_max_columns(table):
    # get max number of columns in a row
    firstRow = table.xpath('./tr[1]/td')
    nr_cols = 0
    # if there is a colspan in the row, increase by colspan value
    for td in firstRow:
        if td.get('colspan') is not None:
            nr_cols += int(td.get('colspan'))
        else:
            nr_cols += 1
    return nr_cols


# save repl_dict to report folder with name
def save_replacements(repl_dict, name):
    if os.path.exists(gv.path_report + name):
        save_file = open(gv.path_report + name, 'rb')
        old_dict = pickle.load(save_file)
        repl_dict = {**old_dict, **repl_dict}
        save_file.close()
    save_file = open(gv.path_report + name, 'wb')
    pickle.dump(repl_dict, save_file)
    save_file.close()


def add_to_error_log(text):
    gv.list_error_log.append(text)


# this is to split a list in sublists with chunks of consecutive data from the inserted list
def split_non_consecutive(data):
    consec_list = []
    inner_list = []
    for i in range(len(data)):
        if i == 0:
            inner_list = [data[i]]
        elif data[i] == data[i-1] + 1:
            inner_list.append(data[i])
        else:
            consec_list.append(inner_list.copy())
            inner_list.clear()
            inner_list = [data[i]]
    else:
        consec_list.append(inner_list.copy())
    return consec_list
