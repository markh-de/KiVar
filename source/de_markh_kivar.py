import kivar
import pcbnew
import wx
import wx.lib.agw.hyperlink as hyperlink
from os import path as os_path

# TODO:
#
# * Add a Setup plugin (separate button) that defines DNP->NoPos/NoBom behavior. Having this in a separate dialog (which
#   also takes care of nonvolatile storage of the settings) removes any dynamic reload/refresh requirements.
#   (Setup plugin shall have similar icon with wrench in the foreground.)
#
# * Setup plugin: Save option settings as some object in PCB (board variables or text box)
#
# * After applying configuration, define board variables containing the choice for each aspect, e.g. ${KIVAR.BOOT_SEL} => NAND
#   (requires KiCad API change/fix: https://gitlab.com/kicad/code/kicad/-/issues/16426)

class VariantPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'KiVar'
        self.category = 'Assembly Variants'
        self.description = 'Switches predefined assembly variant choices'
        self.icon_file_name      = os_path.join(os_path.dirname(__file__), 'de_markh_kivar-icon-light.png')
        self.dark_icon_file_name = os_path.join(os_path.dirname(__file__), 'de_markh_kivar-icon-dark.png')

    def Run(self):
        board = pcbnew.GetBoard()
        vardict, errors = kivar.get_vardict(board)
        if len(errors) > 0:
            ShowErrorDialog('Rule errors', errors, board)
        elif len(vardict) == 0:
            ShowMissingRulesDialog()
        else:
            ShowVariantDialog(board, vardict)

def version():
    return kivar.version()

def help_url():
    return 'https://github.com/markh-de/KiVar/blob/main/README.md#usage'

def ShowVariantDialog(board, vn_dict):
    dlg = VariantDialog(board, vn_dict)
    dlg.ShowModal()

def pcbnew_parent_window():
    return wx.FindWindowByName('PcbFrame')

class VariantDialog(wx.Dialog):
    def __init__(self, board, vn_dict):
        super().__init__(pcbnew_parent_window(), title=f'KiVar {version()}: Variant Selection', style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.board = board
        self.vardict = vn_dict
        choice_dict = kivar.get_choice_dict(self.vardict)
        preselect = kivar.detect_current_choices(self.board, self.vardict)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Selections
#        sel_grid = wx.GridSizer(cols=2, hgap=10, vgap=6)
        sel_grid = wx.GridSizer(cols=1, hgap=10, vgap=6)

        # left: variations
        var_box = wx.StaticBox(self, label='Variation Choices')
        var_box_sizer = wx.StaticBoxSizer(var_box)
        var_grid = wx.GridSizer(cols=2, hgap=10, vgap=6)

        self.choices = {}
        for cfg in sorted(choice_dict, key=kivar.natural_sort_key):
            opts = ['<unset>']
            sorted_choices = sorted(choice_dict[cfg], key=kivar.natural_sort_key)
            opts.extend(sorted_choices)
            self.choices[cfg] = wx.Choice(self, choices=opts)
            sel_opt = preselect[cfg]
            sel_index = 0 # <unset> by default
            if sel_opt != '':
                sel_index = sorted_choices.index(sel_opt) + 1
            self.choices[cfg].SetSelection(sel_index)
            self.choices[cfg].Bind(wx.EVT_CHOICE, self.on_change)
            
            var_grid.Add(wx.StaticText(self, label=f'{cfg}:'), 1, wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
            var_grid.Add(self.choices[cfg], 0, wx.EXPAND)

        var_box_sizer.Add(var_grid, 1, wx.EXPAND | wx.ALL, 6)
        sel_grid.Add(var_box_sizer, 1, wx.EXPAND | wx.ALL, 4)

        # # right: options
        # opt_box = wx.StaticBox(self, label='Options')
        # reset_button = wx.Button(self, label='Reset Choices')
        # checkbox_excl_from_bom = wx.CheckBox(self, label="DNP sets 'Exclude from bill of materials'")
        # checkbox_excl_from_pos = wx.CheckBox(self, label="DNP sets 'Exclude from position files'")
        # opt_box_sizer = wx.StaticBoxSizer(opt_box, wx.VERTICAL)
        # opt_box_sizer.Add(checkbox_excl_from_bom, 0, wx.EXPAND | wx.ALL, 4)
        # opt_box_sizer.Add(checkbox_excl_from_pos, 0, wx.EXPAND | wx.ALL, 4)
        # opt_box_sizer.Add(wx.StaticText(self, label=''), 1, wx.EXPAND | wx.ALL)
        # opt_box_sizer.Add(reset_button, 0, wx.ALIGN_CENTRE_HORIZONTAL | wx.ALL, 4)
        # opt_box_sizer.Add(wx.StaticText(self, label=''), 1, wx.EXPAND | wx.ALL)
        # sel_grid.Add(opt_box_sizer, 0, wx.EXPAND | wx.ALL, 4)

        sizer.Add(sel_grid, 0, wx.EXPAND | wx.ALL, 4)

        # Changes Text
        changes_box = wx.StaticBox(self, label='Changes To Be Applied')
        self.changes_box_sizer = wx.StaticBoxSizer(changes_box)
        self.changes_box_sizer.SetMinSize((640, 280))

        self.changes_list_win = wx.ScrolledWindow(self, wx.ID_ANY)
        self.changes_list = PcbItemListBox(self.changes_list_win, board)

        self.update_list()

        changes_list_sizer = wx.BoxSizer(wx.VERTICAL)
        changes_list_sizer.Add(self.changes_list, 1, wx.EXPAND | wx.ALL, 3)

        self.changes_list_win.SetSizer(changes_list_sizer)
        self.changes_box_sizer.Add(self.changes_list_win, 1, wx.EXPAND)

        sizer.Add(self.changes_box_sizer, 1, wx.EXPAND | wx.ALL, 8)

        # Bottom (help link and buttons)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        link = hyperlink.HyperLinkCtrl(self, -1, 'Usage hints', URL=help_url())
        default_color = wx.Colour()
        link.SetColours(link=default_color, visited=default_color)
        link.SetToolTip('Opens a web browser at ' + help_url())
        link.EnableRollover(False)

        ok_button = wx.Button(self, label='Update PCB')
#        update_button = wx.Button(self, label='Reset Choices')
        cancel_button = wx.Button(self, label='Close')

        button_sizer.Add(link, 0)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(cancel_button, 0)
#        button_sizer.Add(update_button, 0, wx.LEFT, 6)
        button_sizer.Add(ok_button, 0, wx.LEFT, 6)

        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 8)

        self.SetSizerAndFit(sizer)
        # TODO avoid 50/50 split between boxes. should be dynamic!

        self.Fit()
        self.CentreOnParent()

        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
#        update_button.Bind(wx.EVT_BUTTON, self.on_update)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

    def selections(self):
        s = {}
        for choice in self.choices:
            sel_value = self.choices[choice].GetStringSelection()
            if self.choices[choice].GetSelection() < 1:
                sel_value = '' # <unset>, do not apply to values
            s[choice] = sel_value

        return s

    def on_ok(self, event):
        kivar.apply_choices(self.board, self.vardict, self.selections())
        pcbnew.Refresh()
        self.Destroy()

    def on_change(self, event):
        self.update_list()

#    def on_update(self, event):
#        self.update_text()

    def on_cancel(self, event):
        self.Destroy()

    def update_list(self):
        changes = kivar.apply_choices(self.board, self.vardict, self.selections(), True)
        self.changes_list.setItemList(changes)

def ShowMissingRulesDialog():
    dialog = MissingRulesDialog()
    dialog.ShowModal()
    dialog.Destroy()

class MissingRulesDialog(wx.Dialog):
    def __init__(self):
        super().__init__(pcbnew_parent_window(), title=f'KiVar {version()}: No rule definitions found', style=wx.DEFAULT_DIALOG_STYLE)

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(self, label='Please consult the KiVar documentation to learn how to\nassign variation rules to symbols/footprints:'), 0, wx.ALL, 10)

        sizer.AddSpacer(15)

        link = hyperlink.HyperLinkCtrl(self, -1, help_url(), URL='')
        default_color = wx.Colour()
        link.SetColours(link=default_color, visited=default_color)
        link.SetToolTip('')
        link.EnableRollover(False)
        sizer.Add(link, 0, wx.ALIGN_CENTRE, wx.ALL, 10)

        sizer.AddSpacer(15)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, 'Close')
        button_sizer.Add(ok_button, 0, wx.ALIGN_CENTRE | wx.ALL, 10)

        sizer.Add(button_sizer, 0, wx.ALIGN_CENTRE)
        ok_button.SetFocus()

        self.SetSizerAndFit(sizer)

def ShowErrorDialog(title, errors, board = None):
    dialog = PcbItemListDialog(f'KiVar {version()}: {title}', errors, board)
    dialog.ShowModal()
    dialog.Destroy()

class PcbItemListBox(wx.ListBox):
    def __init__(self, parent, board = None):
        super().__init__(parent)
        self.board = board
        self.refs = []
        self.Bind(wx.EVT_LISTBOX, self.onListItemSelected)

    def setItemList(self, itemlist):
        # current selection gets reset automatically
        self.refs = []
        self.Clear()
        for item in itemlist:
            self.refs.append(item[0])
            self.Append(item[1])

    def onListItemSelected(self, event):
        if self.board is not None:
            ref = self.refs[self.GetSelection()]
            if ref is not None:
                fp = self.board.FindFootprintByReference(ref)
                if fp is not None:
                    wrap_FocusOnItem(fp)

class PcbItemListDialog(wx.Dialog):
    def __init__(self, title, itemlist, board = None):
        super().__init__(pcbnew_parent_window(), title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, size=(800, 500))
        self.refs = []
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Error messages
        errors_box = wx.StaticBox(self, label='Errors')
        errors_box_sizer = wx.StaticBoxSizer(errors_box)
        errors_box_sizer.SetMinSize((640, 280))

        errors_list_win = wx.ScrolledWindow(self, wx.ID_ANY)
        errors_list = PcbItemListBox(errors_list_win, board)
        errors_list.setItemList(itemlist)

        errors_list_sizer = wx.BoxSizer(wx.VERTICAL)
        errors_list_sizer.Add(errors_list, 1, wx.EXPAND | wx.ALL, 3)

        errors_list_win.SetSizer(errors_list_sizer)
        errors_box_sizer.Add(errors_list_win, 1, wx.EXPAND)

        sizer.Add(errors_box_sizer, 1, wx.EXPAND | wx.ALL, 8)

        link = hyperlink.HyperLinkCtrl(self, -1, 'Rule implementation hints', URL=help_url())
        default_color = wx.Colour()
        link.SetColours(link=default_color, visited=default_color)
        link.SetToolTip('Opens a web browser at ' + help_url())
        link.EnableRollover(False)
        self.ok_button = wx.Button(self, wx.ID_OK, 'Close')

        # Bottom (help link and button)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(link, 0)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(self.ok_button, 0)

        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(sizer)

        self.ok_button.SetFocus()

VariantPlugin().register()
