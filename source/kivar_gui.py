import os
import json
import wx
import pcbnew

from .kivar_engine  import * # TODO clean-up
from .kivar_version import version
from . import kivar_gui_custom as custom
from . import kivar_forms as forms

# Note: This GUI can (currently) only be used from within a running pcbnew session.

def doc_vcs_ref():
    return f'v{version()}'

def doc_base_url():
    return f'https://doc.kivar.markh.de/{doc_vcs_ref()}/README.md'

def window_suffix():
    return f' | KiVar {version()}'

class Config:
    MAIN_WIN  = 'main_window'
    ERROR_WIN = 'error_window'
    WIN_SIZE  = 'size'

    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'kivar_config.json')
        self.config_data = {}
        if os.path.exists(self.config_file):
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

def help_url():
    return f'{doc_base_url()}#usage'

def help_migrate_url():
    return f'{doc_base_url()}#migrate'

def platform_str():
    return wx.PlatformInformation().GetPortIdShortName()

def unset_str():
    return '-- unspecified --'

def pcbnew_parent_window():
    return wx.FindWindowByName('PcbFrame')

def dialog_base_config(dialog):
    theme = 'dark' if dialog.GetBackgroundColour().GetLuminance() < 0.5 else 'light'
    dialog.SetIcon(wx.Icon(os.path.join(os.path.dirname(__file__), f'de_markh_kivar-icon-{theme}.png'), wx.BITMAP_TYPE_PNG))
    dialog.SetTitle(dialog.GetTitle() + window_suffix())

def show_selection_dialog(board, fpdict, vardict, parent=pcbnew_parent_window()):
    exit_ui = False
    rect = None
    while not exit_ui:
        variant_info = VariantInfo(board.GetFileName())
        errors = variant_info.read_csv(get_choice_dict(vardict))
        if errors:
            show_error_dialog([['', '', 'Variant Table: '+error] for error in errors])
            exit_ui = True
        else:
            dialog = GuiVariantDialog(parent, board, fpdict, vardict, variant_info)
            if rect is not None:
                dialog.SetRect(rect)
            else:
                dialog.SetSize(Config().get_window_size(Config.MAIN_WIN))
                dialog.CentreOnParent()
            result = dialog.ShowModal()
            rect = dialog.GetRect()
            Config().set_window_size(Config.MAIN_WIN, dialog.GetSize()).save()
            dialog.Destroy()
            if result == wx.ID_OK:
                apply_selection(fpdict, vardict, dialog.selections())
                store_fpdict(board, fpdict)
                pcbnew.Refresh()
            if result != wx.ID_REFRESH:
                exit_ui = True

def show_error_dialog(errors, board=None, parent=pcbnew_parent_window()):
    dialog = GuiErrorListDialog(parent, errors=sorted(errors, key=lambda x: natural_sort_key(x[1])), board=board) # sort by text
    dialog.SetSize(Config().get_window_size(Config.ERROR_WIN))
    dialog.CentreOnParent()
    dialog.ShowModal()
    Config().set_window_size(Config.ERROR_WIN, dialog.GetSize()).save()
    dialog.Destroy()

def show_missing_rules_dialog(legacy_found=0, parent=pcbnew_parent_window()):
    dialog = GuiMissingRulesDialog(parent, legacy_found)
    dialog.ShowModal()
    dialog.Destroy()

class GuiVariantDialog(forms.VariantDialog):
    def __init__(self, parent, board, fpdict, vardict, variant_info):
        super().__init__(parent=parent)
        dialog_base_config(self)
        self.SetMinSize(wx.Size(800, 400))

        self.board = board
        self.fpdict = fpdict
        self.vardict = vardict
        self.variant_info = variant_info

        choice_dict = get_choice_dict(self.vardict)
        self.preselect = detect_current_choices(self.fpdict, self.vardict)

        self.chc_variant.SetItems([unset_str()] + self.variant_info.variants())
        self.chc_variant.SetSelection(0)
        self.chc_variant.Enable(self.variant_info.is_loaded())
        self.chc_variant.Bind(wx.EVT_MOUSEWHEEL, lambda event, target=None: self.on_choice_mousewheel(event, target))

        self.bt_var_menu.set_menu_config(self.menu_var, self.on_menu_update)

        # TODO FUTURE when creating a table, have a checkbox in the naming dialog
        # "Add unspecified aspects for sort order customization?"

        all_aspects = sorted(choice_dict, key=natural_sort_key)
        bound_aspects = self.variant_info.aspects()
        free_aspects = [aspect for aspect in all_aspects if aspect not in bound_aspects]
        enum_aspects = bound_aspects + free_aspects

        self.aspects_gui = {}
        for aspect in enum_aspects:
            is_bound = aspect in bound_aspects
            panel = self.pnl_bound if is_bound else self.pnl_free
            label = wx.StaticText(panel, label=aspect)
            sorted_choices = sorted(choice_dict[aspect], key=natural_sort_key)
            choice = wx.Choice(panel, choices=[unset_str()] + sorted_choices)
            sel_choice = self.preselect[aspect]
            sel_index = 0 if sel_choice is None else sorted_choices.index(sel_choice) + 1
            choice.SetSelection(sel_index)
            choice.Bind(wx.EVT_CHOICE, self.on_aspect_change)
            choice.Bind(wx.EVT_MOUSEWHEEL, lambda event, target=self.scw_bound if is_bound else self.scw_free: self.on_choice_mousewheel(event, target))
            panel.GetSizer().Add(label, 1, wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
            panel.GetSizer().Add(choice, 1, wx.ALIGN_CENTRE_VERTICAL | wx.EXPAND)
            self.aspects_gui[aspect] = (label, choice)

        self.lbx_changes.set_select_handler(self.on_change_item_selected)
        self.update_changes_list()

        # Bottom (help link and buttons)
        legacy_rules = legacy_expressions_found(self.fpdict)
        if legacy_rules:
            target_url = help_migrate_url()
            link_text = f'How to migrate {legacy_rules} found legacy rule(s).'
        else:
            target_url = help_url()
            link_text = 'Help'
        self.link_help.SetLabel(link_text)
        self.link_help.SetURL(target_url)

        self.sdbszOK.SetLabel('Update PCB')
        self.sdbszCancel.SetLabel("Close")

        self.select_matching_variant()

    def on_change_item_selected(self, uuid):
        if self.board is not None and uuid is not None:
            fp = uuid_to_fp(self.board, uuid)
            if fp is not None:
                pcbnew.FocusOnItem(fp)

    def on_menu_update(self, menu):
        vi = self.variant_info
        file_path = vi.file_path()
        can_edit_file = file_path is not None and os.path.exists(file_path) and os.access(file_path, os.W_OK)
        bound = self.variant_info.aspects()
        all_bound_specified = True
        none_specified = True
        for aspect, (label, choice) in self.aspects_gui.items():
            if choice.GetSelection() > 0:
                none_specified = False
            else:
                if aspect in bound:
                    all_bound_specified = False

        self.mi_create_defs.Enable((file_path is not None) and (not none_specified) and (not vi.is_loaded()))
        self.mi_add_def.Enable(all_bound_specified and vi.is_loaded() and self.chc_variant.GetSelection() == 0)
        self.mi_edit_defs.Enable(can_edit_file)
        self.mi_del_def.Enable(vi.is_loaded() and self.chc_variant.GetSelection() > 0)

    def on_mi_create_defs(self, event):
        if self.variant_info.file_path() is None: return # not allowed, should be blocked from menu
        sel = {}
        for aspect, (label, choice) in self.aspects_gui.items():
            if choice.GetSelection() > 0:
                sel[aspect] = choice.GetStringSelection()
        if len(sel) == 0: return # not allowed, should be blocked from menu
        dialog = GuiCreateTableDialog(self, sel)
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            varid = dialog.txc_varid.GetValue()
            if self.variant_file_write_allowed():
                self.variant_info.create_table(varid, sorted(sel, key=natural_sort_key), sel)
                self.variant_info.write_csv()
                self.EndModal(wx.ID_REFRESH)
        dialog.Destroy()

    def on_mi_add_def(self, event):
        if not self.variant_info.is_loaded(): return # not allowed, should be blocked from menu
        bound = self.variant_info.aspects()
        sel = {}
        for aspect, (label, choice) in self.aspects_gui.items():
            if aspect in bound:
                if choice.GetSelection() > 0:
                    sel[aspect] = choice.GetStringSelection()
                else:
                    return # all bound choices must be specified, should be blocked
        dialog = GuiAddVariantDialog(self, sel)
        dialog.set_existing_varids(self.variant_info.variants())
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            if not dialog.entered_varid_exists(): # blocked, but double-check
                if self.variant_file_write_allowed():
                    self.variant_info.add_variant(dialog.entered_varid(), sel)
                    self.variant_info.write_csv()
                    self.EndModal(wx.ID_REFRESH)
        dialog.Destroy()

    def on_mi_edit_defs(self, event):
        wx.LaunchDefaultApplication(self.variant_info.file_path())

    def on_mi_del_def(self, event):
        if self.chc_variant.GetSelection() == 0: return # blocked, but double-check
        varid = self.chc_variant.GetStringSelection()
        if self.variant_info.variants() == [varid]:
            dialog = wx.MessageDialog(self, f'Deleting the definition of the last variant identifier will cause the table file to be removed as well.\nYou will therefore lose all your aspect bindings.\n\nAre you sure you want to remove the variant identifier "{varid}" and all aspect bindings?', 'Delete Last Variant Definition', style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_WARNING)
        else:
            dialog = wx.MessageDialog(self, f'Are you sure you want to remove the variant identifier "{varid}"?', 'Delete Variant Definition', style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_WARNING)
        answer = dialog.ShowModal()
        dialog.Destroy()
        if answer == wx.ID_YES:
            if self.variant_file_write_allowed():
                self.variant_info.delete_variant(varid)
                self.variant_info.write_csv()
                self.EndModal(wx.ID_REFRESH)

    def on_mi_reload(self, event):
        self.EndModal(wx.ID_REFRESH)

    def selections(self):
        sel = {}
        for aspect, (label, choice) in self.aspects_gui.items():
            index = choice.GetSelection()
            sel[aspect] = choice.GetStringSelection() if index > 0 else None
        return sel

    def highlight_changed_aspects(self):
        for aspect, (label, choice) in self.aspects_gui.items():
            selected = choice.GetSelection()
            selected_str = choice.GetStringSelection()
            changed = selected_str != self.preselect[aspect] if selected > 0 else False
            font = label.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD if changed else self.GetFont().GetWeight())
            label.SetFont(font)
            label.Refresh()

    def variant_file_write_allowed(self):
        if self.variant_info.file_has_changed():
            # TODO use yesnocancel and set labels for buttons accordingly: Overwrite / Reload and Reset / Cancel
            dialog = wx.MessageDialog(self, 'File content on disk has changed since loading.\nYou should either reload the file using the menu option "Reload and Reset", or revert to the known file state externally.\n\nDo you want to continue and overwrite the external changes?', 'File Changed on Disk', style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
            answer = dialog.ShowModal()
            dialog.Destroy()
            return answer == wx.ID_YES
        else:
            return True

    def on_variant_change(self, event):
        index = self.chc_variant.GetSelection()
        if index > 0:
            index -= 1
            variant = self.variant_info.variants()[index]
            dd = self.variant_info.choices()
            choices = dd[variant]
            for aspect_index, aspect in enumerate(self.variant_info.aspects()):
                choice_str = choices[aspect_index]
                choice_gui = self.aspects_gui[aspect][1]
                choice_idx = choice_gui.FindString(choice_str, caseSensitive=True)
                choice_gui.SetSelection(choice_idx)
            self.on_aspect_change(None)
        else:
            self.select_matching_variant()

    def select_matching_variant(self):
        sel = self.selections()
        match = self.variant_info.match_variant(sel)
        if match is None:
            self.chc_variant.SetSelection(0)
        else:
            sel_index = self.chc_variant.FindString(match, caseSensitive=True)
            self.chc_variant.SetSelection(sel_index)

    def on_aspect_change(self, event):
        if event is not None: # if None, we were called manually, avoid recursion!
            self.select_matching_variant()
        self.highlight_changed_aspects()
        self.update_changes_list()
        self.Layout()

    def update_changes_list(self):
        changes = apply_selection(self.fpdict, self.vardict, self.selections(), True)
        self.lbx_changes.set_item_list(sorted(changes, key=lambda x: natural_sort_key(x[1])))

    @staticmethod
    def on_choice_mousewheel(event, target):
        if target is not None:
            scroll_x, scroll_y = target.GetViewStart()
            pixels_per_unit_x, pixels_per_unit_y = target.GetScrollPixelsPerUnit()
            step = event.GetLinesPerAction() * event.GetWheelRotation() // event.GetWheelDelta()
            target.Scroll(scroll_x, max(scroll_y - step, 0))

class GuiCreateTableDialog(forms.CreateTableDialog):
    def __init__(self, parent, choice_dict):
        super().__init__(parent=parent)
        # child dialog, hence no base config
        sel = []
        for aspect in sorted(choice_dict, key=natural_sort_key):
            sel.append(f'• {aspect} = {choice_dict[aspect]}')
        self.txt_aspects.SetLabelText('\n'.join(sel))
        self.Fit()
        self.CenterOnParent()

    def on_confirm(self, event):
        if not self.entered_varid().strip():
            wx.MessageBox(f'Please choose a valid variant identifier name.', 'Invalid Variant Identifier', style=wx.ICON_ERROR, parent=self)
        else:
            self.EndModal(wx.ID_OK)

    def entered_varid(self):
        return self.txc_varid.GetValue()

class GuiAddVariantDialog(forms.AddVariantDialog):
    def __init__(self, parent, choice_dict):
        super().__init__(parent=parent)
        # child dialog, hence no base config
        sel = []
        self.existing_varids = []
        for aspect in sorted(choice_dict, key=natural_sort_key):
            sel.append(f'• {aspect} = {choice_dict[aspect]}')
        self.txt_aspects.SetLabelText('\n'.join(sel))
        self.Fit()
        self.CenterOnParent()

    def set_existing_varids(self, varids):
        self.existing_varids = varids

    def entered_varid_exists(self):
        return self.entered_varid() in self.existing_varids

    def on_confirm(self, event):
        if not self.entered_varid().strip():
            wx.MessageBox(f'Please choose a valid variant identifier name.', 'Invalid Variant Identifier', style=wx.ICON_ERROR, parent=self)
        elif self.entered_varid_exists():
            wx.MessageBox(f'The variant identifier "{self.entered_varid()}" already exists.\nPlease choose a different variant identifier name.', 'Conflicting Variant Identifier', style=wx.ICON_ERROR, parent=self)
        else:
            self.EndModal(wx.ID_OK)

    def entered_varid(self):
        return self.txc_varid.GetValue()

class GuiMissingRulesDialog(forms.MissingRulesDialog):
    def __init__(self, parent, legacy_found=0):
        super().__init__(parent=parent)
        dialog_base_config(self)
        if legacy_found: # override text and URL
            self.txt_info.SetLabelMarkup(f'KiVar could not find any rules in the current format.\n\nHowever, there were found <b>{legacy_found} rule(s) in the legacy format</b>, which\nis not supported anymore.\n\nPlease consult the KiVar documentation to learn how to\nmigrate the rules of your existing designs to the current format.')
            self.link_help.SetLabel('KiVar Migration Guide')
            self.link_help.SetURL(help_migrate_url())
        else:
            self.link_help.SetLabel('KiVar Usage Guide')
            self.link_help.SetURL(help_url())
        self.btn_close.SetFocus()
        self.Fit()
        self.CenterOnParent()

class GuiErrorListDialog(forms.ErrorListDialog):
    def __init__(self, parent, errors=None, board=None):
        super().__init__(parent=parent)
        dialog_base_config(self)
        self.board = board

        self.lbx_errors.set_item_list(errors)
        self.lbx_errors.set_select_handler(self.on_item_selected)

        self.btn_close.SetFocus()
        self.Fit()
        self.CenterOnParent()

    def on_item_selected(self, uuid):
        if self.board is not None and uuid is not None:
            fp = uuid_to_fp(self.board, uuid)
            if fp is not None:
                pcbnew.FocusOnItem(fp)
