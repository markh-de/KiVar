from os import path as os_path
import wx
import wx.lib.agw.hyperlink as hyperlink
import pcbnew
try:
    from kivar_backend import build_fpdict, build_vardict, version, get_choice_dict, detect_current_choices, natural_sort_key, apply_selection, store_fpdict, uuid_to_fp, pcbnew_compatibility_error, legacy_expressions_found
except ModuleNotFoundError:
    from .kivar_backend import build_fpdict, build_vardict, version, get_choice_dict, detect_current_choices, natural_sort_key, apply_selection, store_fpdict, uuid_to_fp, pcbnew_compatibility_error, legacy_expressions_found

def doc_vcs_ref():
    return f'v{version()}'

def doc_base_url():
    return f'https://doc.kivar.markh.de/{doc_vcs_ref()}/README.md'

class KiVarPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'KiVar: Switch Assembly Variants'
        self.category = 'Assembly Variants'
        self.description = 'Switch between predefined assembly variant choices'
        self.icon_file_name      = os_path.join(os_path.dirname(__file__), 'de_markh_kivar-icon-light.png')
        self.dark_icon_file_name = os_path.join(os_path.dirname(__file__), 'de_markh_kivar-icon-dark.png')
        self.show_toolbar_button = True

    def Run(self):
        compatibility_problem = pcbnew_compatibility_error()
        if compatibility_problem is not None:
            wx.MessageBox(message=compatibility_problem, caption=f'KiVar {version()}: Compatibility problem', style=wx.ICON_ERROR)
            return
        board = pcbnew.GetBoard()
        fpdict = build_fpdict(board)
        vardict, errors = build_vardict(fpdict)
        if len(errors) > 0:
            show_error_dialog('Rule errors', errors, board)
        elif len(vardict) == 0:
            show_missing_rules_dialog(legacy_expressions_found(fpdict))
        else:
            show_selection_dialog(board, fpdict, vardict)

def help_url():
    return f'{doc_base_url()}#usage'

def help_migrate_url():
    return f'{doc_base_url()}#migrate'

def show_selection_dialog(board, fpdict, vardict):
    dlg = VariantDialog(board, fpdict, vardict)
    dlg.ShowModal()

def pcbnew_parent_window():
    return wx.FindWindowByName('PcbFrame')

class VariantDialog(wx.Dialog):
    def __init__(self, board, fpdict, vardict):
        super().__init__(pcbnew_parent_window(), title=f'Variant Selection | KiVar {version()}', style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)

        self.board = board
        self.vardict = vardict
        self.fpdict = fpdict

        choice_dict = get_choice_dict(self.vardict)
        preselect = detect_current_choices(self.fpdict, self.vardict)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Variation Selections
        var_box = wx.StaticBox(self, label='Variation Aspect Choices')
        var_box_sizer = wx.StaticBoxSizer(var_box)

        scroll_panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scroll_panel.SetScrollRate(8, 8)

        var_grid = wx.GridSizer(cols=2, hgap=10, vgap=6)
        self.choices = {}
        for cfg in sorted(choice_dict, key=natural_sort_key):
            opts = ['<unset>']
            sorted_choices = sorted(choice_dict[cfg], key=natural_sort_key)
            opts.extend(sorted_choices)
            self.choices[cfg] = wx.Choice(scroll_panel, choices=opts)
            sel_opt = preselect[cfg]
            sel_index = 0 # <unset> by default
            if sel_opt is not None:
                sel_index = sorted_choices.index(sel_opt) + 1
            self.choices[cfg].SetSelection(sel_index)
            self.choices[cfg].Bind(wx.EVT_CHOICE, self.on_change)
            
            var_grid.Add(wx.StaticText(scroll_panel, label=f'{cfg}:'), 1, wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
            var_grid.Add(self.choices[cfg], 0, wx.EXPAND)

        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        scroll_sizer.Add(var_grid, 0, wx.EXPAND | wx.ALL, 8)

        scroll_panel.SetSizer(scroll_sizer)

        var_box_sizer.Add(scroll_panel, 1, wx.ALL | wx.EXPAND, 5)
        var_box_sizer.SetMinSize((640, 300))

        sizer.Add(var_box_sizer, 12, wx.EXPAND | wx.ALL, 8)

        # Changes Text
        changes_box = wx.StaticBox(self, label='Changes To Be Applied')
        self.changes_box_sizer = wx.StaticBoxSizer(changes_box)

        self.changes_list_win = wx.ScrolledWindow(self, wx.ID_ANY)
        self.changes_list = PcbItemListBox(self.changes_list_win, board)

        self.update_list()

        changes_list_sizer = wx.BoxSizer(wx.VERTICAL)
        changes_list_sizer.Add(self.changes_list, 1, wx.EXPAND | wx.ALL, 3)

        self.changes_list_win.SetSizer(changes_list_sizer)
        self.changes_box_sizer.Add(self.changes_list_win, 1, wx.EXPAND)

        sizer.Add(self.changes_box_sizer, 10, wx.EXPAND | wx.ALL, 8)

        # Bottom (help link and buttons)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        legacy_rules = legacy_expressions_found(self.fpdict)
        if legacy_rules:
            target_url = help_migrate_url()
            link_text = f'Read how to migrate {legacy_rules} found legacy rule(s).'
        else:
            target_url = help_url()
            link_text = 'Usage hints'
        link = hyperlink.HyperLinkCtrl(self, -1, link_text, URL=target_url)
        default_color = wx.Colour()
        link.SetColours(link=default_color, visited=default_color)
        link.SetToolTip(f'Opens a web browser at {target_url}')
        link.EnableRollover(False)

        ok_button = wx.Button(self, label='Update PCB')
        cancel_button = wx.Button(self, label='Close')

        button_sizer.Add(link, 0)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(cancel_button, 0)
        button_sizer.Add(ok_button, 0, wx.LEFT, 6)

        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 8)

        self.SetSizerAndFit(sizer)
        self.CentreOnParent()

        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

    def selections(self):
        s = {}
        for choice in self.choices:
            sel_value = self.choices[choice].GetStringSelection()
            if self.choices[choice].GetSelection() < 1:
                sel_value = None # <unset>, do not apply to values
            s[choice] = sel_value

        return s

    def on_ok(self, event):
        apply_selection(self.fpdict, self.vardict, self.selections())
        store_fpdict(self.board, self.fpdict)
        pcbnew.Refresh()
        self.Destroy()

    def on_change(self, event):
        self.update_list()

    def on_cancel(self, event):
        self.Destroy()

    def update_list(self):
        changes = apply_selection(self.fpdict, self.vardict, self.selections(), True)
        self.changes_list.set_item_list(sorted(changes, key=lambda x: natural_sort_key(x[1])))

def show_missing_rules_dialog(legacy_found=0):
    dialog = MissingRulesDialog(legacy_found)
    dialog.ShowModal()
    dialog.Destroy()

class MissingRulesDialog(wx.Dialog):
    def __init__(self, legacy_found=0):
        super().__init__(pcbnew_parent_window(), title=f'KiVar {version()}: No rule definitions found', style=wx.DEFAULT_DIALOG_STYLE)

        sizer = wx.BoxSizer(wx.VERTICAL)

        if legacy_found:
            text = f'KiVar could not find any valid rules in the current format.\n\nHowever, there were found {legacy_found} rule(s) in the legacy format, which\nis unsupported in this release.\n\nPlease consult the KiVar documentation to learn how to\nmigrate the rules of your existing designs to the current format:'
            link = help_migrate_url()
        else:
            text = 'KiVar could not find any valid rules.\n\nPlease consult the KiVar documentation to learn how to\nassign variation rules to symbols/footprints:'
            link = help_url()
        sizer.Add(wx.StaticText(self, label=text), 0, wx.ALL, 20)

        link = hyperlink.HyperLinkCtrl(self, -1, link, URL='')
        default_color = wx.Colour()
        link.SetColours(link=default_color, visited=default_color)
        link.SetToolTip('')
        link.EnableRollover(False)
        sizer.Add(link, 0, wx.ALIGN_CENTRE | wx.ALL, 20)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, 'Close')
        button_sizer.Add(ok_button, 0, wx.ALIGN_CENTRE | wx.ALL, 20)

        sizer.Add(button_sizer, 0, wx.ALIGN_CENTRE)
        ok_button.SetFocus()

        self.SetSizerAndFit(sizer)

def show_error_dialog(title, errors, board=None):
    dialog = PcbItemListDialog(f'KiVar {version()}: {title}', sorted(errors, key=lambda x: natural_sort_key(x[1])), board) # sort by text
    dialog.ShowModal()
    dialog.Destroy()

class PcbItemListBox(wx.ListBox):
    def __init__(self, parent, board=None):
        super().__init__(parent)
        self.board = board
        self.uuids = []
        self.Bind(wx.EVT_LISTBOX, self.on_list_item_selected)

    def set_item_list(self, item_list):
        # current selection gets reset automatically
        self.uuids = []
        self.Clear()
        for item in item_list:
            self.uuids.append(item[0])
            self.Append(item[2])

    def on_list_item_selected(self, event):
        if self.board is not None:
            uuid = self.uuids[self.GetSelection()]
            if uuid is not None:
                fp = uuid_to_fp(self.board, uuid)
                if fp is not None:
                    pcbnew.FocusOnItem(fp)

class PcbItemListDialog(wx.Dialog):
    def __init__(self, title, itemlist, board=None):
        super().__init__(pcbnew_parent_window(), title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, size=(800, 500))
        self.refs = []
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Error messages
        errors_box = wx.StaticBox(self, label='Errors')
        errors_box_sizer = wx.StaticBoxSizer(errors_box)
        errors_box_sizer.SetMinSize((640, 280))

        errors_list_win = wx.ScrolledWindow(self, wx.ID_ANY)
        errors_list = PcbItemListBox(errors_list_win, board)
        errors_list.set_item_list(itemlist)

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

KiVarPlugin().register()
