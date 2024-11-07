from os import path as os_path
import json
import wx
import wx.lib.agw.hyperlink as hyperlink
import pcbnew
try:                        from  kivar_backend import *
except ModuleNotFoundError: from .kivar_backend import *

def doc_vcs_ref():
    return f'v{version()}'

def doc_base_url():
    return f'https://doc.kivar.markh.de/{doc_vcs_ref()}/README.md'

class Config:
    MAIN_WIN  = 'main_window'
    ERROR_WIN = 'error_window'
    WIN_SIZE  = 'size'

    def __init__(self):
        self.config_file = os_path.join(os_path.dirname(__file__), 'kivar_config.json')
        self.config_data = {}
        if os_path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config_data = json.load(f)
        self.inherit_defaults(
            {
                Config.MAIN_WIN:  { Config.WIN_SIZE: [900, 680] },
                Config.ERROR_WIN: { Config.WIN_SIZE: [800, 480] }
            }
        )

    def inherit_defaults(self, default_data):
        Config._extend_config(self.config_data, default_data)

    @staticmethod
    def _extend_config(config_data, default_data):
        for key, default_value in default_data.items():
            if not key in config_data:
                config_data[key] = default_value
            elif isinstance(config_data[key], dict) and isinstance(default_value, dict):
                Config._extend_config(config_data[key], default_value)

    def get_window_size(self, window_key):
        return wx.Size(self.config_data[window_key][Config.WIN_SIZE])

    def set_window_size(self, window_key, window_size):
        self.config_data[window_key][Config.WIN_SIZE] = [window_size.GetWidth(), window_size.GetHeight()]
        return self

    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(dict(sorted(self.config_data.items())), f)

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
            wx.MessageBox(message=compatibility_problem, caption=f'Compatibility Problem | KiVar {version()}', style=wx.ICON_ERROR)
            return
        board = pcbnew.GetBoard()
        fpdict = build_fpdict(board)
        vardict, errors = build_vardict(fpdict)
        if len(errors) > 0:
            show_error_dialog(errors, board)
        elif len(vardict) == 0:
            show_missing_rules_dialog(legacy_expressions_found(fpdict))
        else:
            show_selection_dialog(board, fpdict, vardict)

def help_url():
    return f'{doc_base_url()}#usage'

def help_migrate_url():
    return f'{doc_base_url()}#migrate'

def pcbnew_parent_window():
    return wx.FindWindowByName('PcbFrame')

def show_selection_dialog(board, fpdict, vardict):
    dialog = VariantDialog(board, fpdict, vardict)
    result = dialog.ShowModal()
    dialog.Destroy()
    if result == wx.ID_OK:
        apply_selection(fpdict, vardict, dialog.selections())
        store_fpdict(board, fpdict)
        pcbnew.Refresh()

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

        scroll_panel = wx.ScrolledWindow(self, style=wx.VSCROLL | wx.HSCROLL)
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

        sizer.Add(var_box_sizer, 12, wx.EXPAND | wx.ALL, 10)

        # Changes Text
        changes_box = wx.StaticBox(self, label='Changes to Be Applied')
        changes_box_sizer = wx.StaticBoxSizer(changes_box)
        self.changes_list = PcbItemListBox(changes_box, board)
        self.changes_list.SetMinSize((360, 100))
        changes_box_sizer.Add(self.changes_list, 1, wx.EXPAND | wx.ALL, 5)
        self.update_list()
        sizer.Add(changes_box_sizer, 10, wx.EXPAND | wx.ALL, 10)

        # Bottom (help link and buttons)
        button_sizer = wx.StdDialogButtonSizer()

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

        ok_button = wx.Button(self, id=wx.ID_OK, label='Update PCB')
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label='Close')

        ok_button.Bind(wx.EVT_BUTTON, self.on_close)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        button_sizer.Add(link, 0, wx.LEFT, 5)
        button_sizer.AddStretchSpacer(1)
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.SetSizerAndFit(sizer)
        self.SetSize(Config().get_window_size(Config.MAIN_WIN))
        self.CentreOnParent()

    def selections(self):
        s = {}
        for choice in self.choices:
            sel_value = self.choices[choice].GetStringSelection()
            if self.choices[choice].GetSelection() < 1:
                sel_value = None # <unset>, do not apply to values
            s[choice] = sel_value

        return s

    def on_change(self, event):
        self.update_list()
        self.Layout()

    def on_close(self, event):
        config = Config().set_window_size(Config.MAIN_WIN, self.GetSize()).save()
        event.Skip()

    def update_list(self):
        changes = apply_selection(self.fpdict, self.vardict, self.selections(), True)
        self.changes_list.set_item_list(sorted(changes, key=lambda x: natural_sort_key(x[1])))

def show_missing_rules_dialog(legacy_found=0):
    dialog = MissingRulesDialog(legacy_found)
    dialog.ShowModal()
    dialog.Destroy()

class MissingRulesDialog(wx.Dialog):
    def __init__(self, legacy_found=0):
        super().__init__(pcbnew_parent_window(), title=f'Missing Rule Definitions | KiVar {version()}', style=wx.DEFAULT_DIALOG_STYLE)

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

def show_error_dialog(errors, board=None):
    dialog = PcbItemListErrorDialog(f'Rule Processing Errors | KiVar {version()}', sorted(errors, key=lambda x: natural_sort_key(x[1])), board) # sort by text
    dialog.ShowModal()
    dialog.Destroy()

class PcbItemListBox(wx.ListBox):
    def __init__(self, parent, board=None):
        super().__init__(parent, style=wx.LB_SINGLE | wx.LB_HSCROLL)
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

class PcbItemListErrorDialog(wx.Dialog):
    def __init__(self, title, itemlist, board=None):
        super().__init__(pcbnew_parent_window(), title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        self.refs = []
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Error messages
        errors_box = wx.StaticBox(self, label='Errors')
        errors_box_sizer = wx.StaticBoxSizer(errors_box)
        errors_list = PcbItemListBox(errors_box, board)
        errors_box_sizer.Add(errors_list, 1, wx.EXPAND | wx.ALL, 5)
        errors_list.set_item_list(itemlist)
        sizer.Add(errors_box_sizer, 1, wx.EXPAND | wx.ALL, 10)
        errors_list.SetMinSize((300, 100))

        link = hyperlink.HyperLinkCtrl(self, -1, 'Rule implementation hints', URL=help_url())
        default_color = wx.Colour()
        link.SetColours(link=default_color, visited=default_color)
        link.SetToolTip('Opens a web browser at ' + help_url())
        link.EnableRollover(False)
        ok_button = wx.Button(self, wx.ID_OK, 'Close')

        # Bottom (help link and button)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(link, 0)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(ok_button, 0)

        sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer.AddSpacer(5)

        self.SetSizerAndFit(sizer)
        self.SetSize(Config().get_window_size(Config.ERROR_WIN))
        self.CentreOnParent()

        ok_button.Bind(wx.EVT_BUTTON, self.on_close)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        ok_button.SetFocus()

    def on_close(self, event):
        config = Config().set_window_size(Config.ERROR_WIN, self.GetSize()).save()
        event.Skip()

KiVarPlugin().register()
