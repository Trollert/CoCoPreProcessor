import global_vars
from tkinter import Listbox, Menu, Text, Tk, Entry

# entryWords = Entry(frameWords, width=50, bg='yellow')
# entryWords.insert(0, 'Click on an item in the listbox')
# entryWords.pack(side='top')
# entryWords.bind('<Return>', partial(set_list, listboxWords, entryWords))


# listbox class that has the option to pop up a menu on list items with right-click
class FancyListbox(Listbox):

    def __init__(self, parent, popup_menu=True,  *args, **kwargs):
        Listbox.__init__(self, parent, *args, **kwargs)
        self.popup_menu = popup_menu
        self.last_entry = 'This is first'
        if self.popup_menu:
            self.popup_menu = Menu(self, tearoff=0)
            self.popup_menu.add_command(label="Add to user words",
                                        command=self.add_user_word)
            self.bind("<Button-3>", self.popup)
        # self.entry_box = Entry(self, bg='PaleGreen1')
        # self.entry_box.pack()
        self.pack(side='top')
        self.bind('<ButtonRelease-1>', self.get_list_element)
    # @classmethod
    def get_list_element(self):
        vw = self.yview()
        # get selected line index
        if self.curselection():
            index = self.curselection()[0]
            # get the line's text

            # delete previous text in enter1
            # entry.delete(0, 100)
            # # # now display the selected text
            # entry.insert(0, text)
            self.yview_moveto(vw[0])
            print(self.get(index))
            self.last_entry = self.get(index)

    def set_list(self, entry, event):
        """
        insert an edited line from the entry widget
        back into the listbox
        """
        vw = self.yview()
        index = self.curselection()[0]

        # delete old listbox line
        self.delete(index)

        # insert edited item back into listbox1 at index
        self.insert(index, entry)
        self.yview_moveto(vw[0])

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


def set_entry_box(list, entry, event):
    """
    function to read the listbox selection
    and put the result in an entry widget
    """
    vw = list.yview()
    # # get selected line index
    index = list.curselection()[0]
    # # get the line's text
    seltext = list.get(index)
    # delete previous text in enter1
    entry.delete(0, 100)
    # now display the selected text
    entry.insert(0, seltext)
    # print(text)
    # list.yview_moveto(vw[0])
