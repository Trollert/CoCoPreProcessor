import global_vars
from tkinter import Listbox, Menu, Text, Tk, ttk, Label, StringVar, Frame, Widget, Scrollbar, Canvas
from functools import partial

# listbox class that has the option to pop up a menu on list items with right-click
class FancyListbox(Listbox):

    def __init__(self, parent, popup_menu=True,  *args, **kwargs):
        Listbox.__init__(self, parent, *args, **kwargs)
        self.popup_menu = popup_menu
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
    textbox = Text(popup, height=40, width=150)
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


class VerticalScrolledFrame:
    """
    A vertically scrolled Frame that can be treated like any other Frame
    ie it needs a master and layout and it can be a master.
    :width:, :height:, :bg: are passed to the underlying Canvas
    :bg: and all other keyword arguments are passed to the inner Frame
    note that a widget layed out in this frame will have a self.master 3 layers deep,
    (outer Frame, Canvas, inner Frame) so
    if you subclass this there is no built in way for the children to access it.
    You need to provide the controller separately.
    """
    def __init__(self, master, **kwargs):
        width = kwargs.pop('width', None)
        height = kwargs.pop('height', None)
        bg = kwargs.pop('bg', kwargs.pop('background', None))
        self.outer = Frame(master, **kwargs)

        self.vsb = Scrollbar(self.outer, orient='vertical')
        self.vsb.pack(fill='y', side='right')
        self.canvas = Canvas(self.outer, highlightthickness=0, width=width, height=height, bg=bg)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas['yscrollcommand'] = self.vsb.set
        # mouse scroll does not seem to work with just "bind"; You have
        # to use "bind_all". Therefore to use multiple windows you have
        # to bind_all in the current widget
        self.canvas.bind("<Enter>", self._bind_mouse)
        self.canvas.bind("<Leave>", self._unbind_mouse)
        self.vsb['command'] = self.canvas.yview

        self.inner = Frame(self.canvas, bg=bg)
        # pack the inner Frame into the Canvas with the topleft corner 4 pixels offset
        self.canvas.create_window(4, 4, window=self.inner, anchor='nw')
        self.inner.bind("<Configure>", self._on_frame_configure)

        self.outer_attr = set(dir(Widget))

    def __getattr__(self, item):
        if item in self.outer_attr:
            # geometry attributes etc (eg pack, destroy, tkraise) are passed on to self.outer
            return getattr(self.outer, item)
        else:
            # all other attributes (_w, children, etc) are passed to self.inner
            return getattr(self.inner, item)

    def _on_frame_configure(self, event=None):
        x1, y1, x2, y2 = self.canvas.bbox("all")
        height = self.canvas.winfo_height()
        self.canvas.config(scrollregion = (0,0, x2, max(y2, height)))

    def _bind_mouse(self, event=None):
        self.canvas.bind_all("<4>", self._on_mousewheel)
        self.canvas.bind_all("<5>", self._on_mousewheel)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mouse(self, event=None):
        self.canvas.unbind_all("<4>")
        self.canvas.unbind_all("<5>")
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        """Linux uses event.num; Windows / Mac uses event.delta"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units" )
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units" )
            
# Colors
colorNoActiveTab = "#CCCCCC"  # Color of the active tab
colorActiveTab = "#EBEBEB"  # Color of the no active tab
colorNoEditedTab = "#c1ffba"
colorEditedTab = "#e6ffe3"

# # Fonts
# fontLabels = 'Calibri'
# sizeLabels2 = 9


class ListboxEditable(object):
    """A class that emulates a listbox, but you can also edit a field"""
    list = []
    # Constructor
    def __init__(self, master_frame, custom_list, popup_menu=False, fontLabels='Calibri', sizeLabels2=9, width=45):
        # *** Assign the first variables ***
        # The frame that contains the ListboxEditable
        self.frameMaster = master_frame
        # List of the initial items
        self.list = list(custom_list)
        # Number of initial rows at the moment
        self.numberRows = len(self.list)
        # manage fonts
        self.fontLabels = fontLabels
        self.sizeLabels = sizeLabels2
        self.width = width
        # remember already changed entries
        self.noChange = []

        self.popup_menu = popup_menu

            # self.popup_menu = Menu(self, tearoff=0)
            # self.popup_menu.add_command(label="Add to user words",
            #                             command=self.add_user_word)
            # self.bind("<Button-3>", self.popup)
            #


        # *** Create the necessary labels ***
        ind = 0
        for row in self.list:
            # Get the name of the label
            labelName = 'label' + str(ind)
            labelMenu = 'menu' + str(ind)
            # Create the variable
            setattr(self, labelName, Label(self.frameMaster, text=self.list[ind], bg=colorNoActiveTab, fg='black',
                                           font=(self.fontLabels, self.sizeLabels), pady=2, padx=2, width=self.width,
                                           anchor='w'))
            # create the menu
            if self.popup_menu:
                setattr(self, labelMenu, Menu(self.frameMaster, tearoff=0))
                # right click open menu
                getattr(self, labelMenu).add_command(label="Add to user words", command=partial(self.add_user_word, ind))

            # command = partial(generate_file, tree, entryCkb)
            # ** Bind actions
            # 1 left click - Change background
            getattr(self, labelName).bind('<Button-1>', lambda event, a=labelName: self.changeBackground(a))
            # Double click - Convert to entry
            getattr(self, labelName).bind('<Double-1>', lambda event, a=ind: self.changeToEntry(a))
            getattr(self, labelName).bind('<Return>', lambda event, a=ind: self.changeToEntry(a))
            # bind right click to popup menu
            if self.popup_menu:
                getattr(self, labelName).bind('<Button-3>', lambda event, a=ind: self.popup(event, a))
            # Move up and down
            getattr(self, labelName).bind("<Up>", lambda event, a=ind: self.up(a))
            getattr(self, labelName).bind("<Down>", lambda event, a=ind: self.down(a))

            # Increase the iterator
            ind = ind + 1

    # *** Add user words popup *** #
    def popup(self, event, ind):
        labelMenu = 'menu' + str(ind)
        try:
            getattr(self, labelMenu).tk_popup(event.x_root, event.y_root, 0)
        finally:
            getattr(self, labelMenu).grab_release()

    def add_user_word(self, ind):
        with open(global_vars.working_folder + '/user_words.txt', 'a', encoding='UTF-8') as f:
            f.write(getattr(self, 'label' + str(ind)).cget('text') + '\n')

    # Place
    def placeListBoxEditable(self):
        # Go row by row placing it
        ind = 0
        for row in self.list:
            # Get the name of the label
            labelName = 'label' + str(ind)
            # Place the variable
            getattr(self, labelName).grid(row=ind, column=0)

            # Increase the iterator
            ind = ind + 1

    # Action to do when one click
    def changeBackground(self, labelNameSelected, edited=False):
        # Ensure that all the remaining labels are deselected
        if edited:
            self.noChange.append(labelNameSelected)
            # Change the background of the corresponding label
            # getattr(self, labelNameSelected).configure(bg=colorEditedTab)
            # self.noChange = list(dict.fromkeys(self.noChange))
        ind = 0
        for row in self.list:
            # Get the name of the label
            labelName = 'label' + str(ind)
            # Place the variable
            if labelName not in self.noChange:
                getattr(self, labelName).configure(bg=colorNoActiveTab)
            else:
                getattr(self, labelName).configure(bg=colorNoEditedTab)
            # Increase the iterator
            ind = ind + 1

        # Change the background of the corresponding label
        if labelNameSelected not in self.noChange:
            getattr(self, labelNameSelected).configure(bg=colorActiveTab)
        else:
            getattr(self, labelNameSelected).configure(bg=colorEditedTab)
        # Set the focus for future bindings (moves)
        getattr(self, labelNameSelected).focus_force()

    # Function to do when up button pressed
    def up(self, ind):
        if ind == 0:  # Go to the last
            # Get the name of the label
            labelName = 'label' + str(self.numberRows - 1)
        else:  # Normal
            # Get the name of the label
            labelName = 'label' + str(ind - 1)

        # Call the select
        self.changeBackground(labelName)

    # Function to do when down button pressed
    def down(self, ind):
        if ind == self.numberRows - 1:  # Go to the last
            # Get the name of the label
            labelName = 'label0'
        else:  # Normal
            # Get the name of the label
            labelName = 'label' + str(ind + 1)

        # Call the select
        self.changeBackground(labelName)

    # Action to do when double-click
    def changeToEntry(self, ind):
        # Variable of the current entry
        labelName = 'label' + str(ind)
        self.entryVar = StringVar()
        self.entryVar.set(getattr(self, labelName).cget('text'))
        # Create the entry
        # entryName='entry'+str(ind) # Name
        self.entryActive = ttk.Entry(self.frameMaster, font=(self.fontLabels, self.sizeLabels), textvariable=self.entryVar,
                                     width=self.width)
        # Place it on the correct grid position
        self.entryActive.grid(row=ind, column=0)
        # Focus to the entry
        self.entryActive.focus_force()
        # print(self.list)

        # Bind the action of focusOut
        self.entryActive.bind("<FocusOut>", lambda event, a=ind: self.saveEntryValue(a)) and \
            self.entryActive.bind("<Return>", lambda event, a=ind: self.saveEntryValue(a))


    def saveEntryValue(self, ind):
        # Find the label to recover
        labelName = 'label' + str(ind)
        self.list[ind] = self.entryVar.get()
        # Remove the entry from the screen
        self.entryActive.grid_forget()
        # Place it again
        getattr(self, labelName).grid(row=ind, column=0)
        # Change the name to the value of the entry
        getattr(self, labelName).configure(text=self.entryVar.get())
        # change background to green
        self.changeBackground(labelName, edited=True)
        # set focus
        # getattr(self, labelName).focus_set()

    def return_list(self):
        return self.list