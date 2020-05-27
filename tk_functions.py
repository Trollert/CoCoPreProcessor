import global_vars


# UI for number checks
def listbox_copy(lb):
    global_vars.tk.clipboard_clear()
    w = lb.widget
    selected = int(w.curselection()[0])
    global_vars.tk.clipboard_append(w.get(selected))


def set_list(list, entry, event):
    """
    insert an edited line from the entry widget
    back into the listbox
    """
    vw = list.yview()
    index = list.curselection()[0]

    # delete old listbox line
    list.delete(index)

    # insert edited item back into listbox1 at index
    list.insert(index, entry.get())
    list.yview_moveto(vw[0])


def get_list(list, entry, event):
    """
    function to read the listbox selection
    and put the result in an entry widget
    """
    vw = list.yview()
    # get selected line index
    index = list.curselection()[0]
    # get the line's text
    seltext = list.get(index)
    # delete previous text in enter1
    entry.delete(0, 100)
    # now display the selected text
    entry.insert(0, seltext)
    list.yview_moveto(vw[0])
