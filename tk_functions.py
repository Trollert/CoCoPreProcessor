import global_vars
from tkinter import Listbox, Menu, Text, Tk

class FancyListbox(Listbox):

    def __init__(self, parent, *args, **kwargs):
        Listbox.__init__(self, parent, *args, **kwargs)

        self.popup_menu = Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Add to user words",
                                    command=self.add_user_word)

        self.bind("<Button-3>", self.popup) # Button-2 on Aqua

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def add_user_word(self):
        with open(global_vars.working_folder + '/user_words.txt', 'a', encoding='UTF-8') as f:
            f.write(self.get(self.curselection()) + '\n')


def display_changelog():
    popup = Tk()
    textbox = Text(popup, height=20, width=100)
    textbox.pack(expand=True, fill='both')
    with open(global_vars.working_folder + '/changelog.txt', 'r') as f:
        textbox.insert('insert', f.read())
    popup.mainloop()


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
