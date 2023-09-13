import pcbnew
import wx
from os import path as os_path

# Used abbreviations:
# * Vn = Variation
# * Ch = Choice

# TODO:
#
# * Use None where applicable (instead of empty string)
#
# * Add options panel incl. "Reset" button, that preselects all choices depending on options (because preselect
#   criteria depend on these checkbox states).
#
# * After applying configuration, define board variables containing the choice for each vn, e.g. ${KIVAR.BOOT_SEL} => NAND
#
# * Save option settings as some object in PCB (text box?)

class VariantPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'KiVar'
        self.category = 'Assembly Variants'
        self.description = 'Switches between predefined assembly variants'
        self.icon_file_name = os_path.join(os_path.dirname(__file__), 'kivar-icon-light.svg')
        self.dark_icon_file_name = os_path.join(os_path.dirname(__file__), 'kivar-icon-dark.svg')

    def Run(self):
        board = pcbnew.GetBoard()
        vn_dict, errors = get_vn_dict(board)
        if len(errors) == 0:
            ShowVariantDialog(board, vn_dict)
        else:
            ShowErrorDialog('Rule errors', errors)

def wrap_HasField(fp, field):
    if pcbnew_version() >= 799:
        return fp.HasField(field)
    else:
        return fp.HasProperty(field)

def wrap_GetField(fp, field):
    if pcbnew_version() >= 799:
        return fp.GetFieldByName(field).GetText()
    else:
        return fp.GetProperty(field)

def pcbnew_version():
    return int(pcbnew.GetMajorMinorPatchVersion().split('.')[0]) * 100 + int(pcbnew.GetMajorMinorPatchVersion().split('.')[1])

def pcbnew_parent_window():
    return wx.FindWindowByName('PcbFrame')

def version():
    return '0.0.3'

def variant_cfg_field_name():
    return 'KiVar.Rule'

def help_url():
    return 'https://github.com/markh-de/KiVar'

def opt_dnp():
    return 'dnp'

def key_val():
    return 'v'

def key_opts():
    return 'o'

def key_default():
    return '*'

def bool_as_text(value):
    return 'true' if value == True else 'false'

def use_attr_dnp():
    return pcbnew_version() >= 799

# TODO impl dedicated option "nbom"?
def use_attr_excl_from_bom():
    return True
#    return api_version() < 799

# TODO impl dedicated option "npos"?
def use_attr_excl_from_posfiles():
    return True
#    return api_version() < 799

def detect_current_choices(board, vn_dict):
    choices = get_choice_dict(vn_dict)

    # How it works:
    # We use the usual Choice dict filled with all possible Choices per Vn.
    # Then we eliminate all Choices whose values do not match the actual FP values (or attributes).
    # If exactly one Choice per Vn remains, then we convert these to a selection dict, which is then
    # filtered to contain only Choices that exactly match the actual FP values and attributes.

    # Step 1: Eliminate Choices not matching the actual FP values.
    for ref in vn_dict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        fp_value = fp.GetValue()
        if use_attr_excl_from_bom():
            fp_excl_bom = fp.IsExcludedFromBOM()
        if use_attr_excl_from_posfiles():
            fp_excl_pos = fp.IsExcludedFromPosFiles()
        if use_attr_dnp():
            fp_dnp = fp.IsDNP()

        for vn in vn_dict[ref]:
            # Check each remaining Choice whether it can be eliminated.
            eliminate_choices = []
            for choice in choices[vn]:
                fp_choice_value = vn_dict[ref][vn][choice][key_val()]
                fp_choice_dnp = opt_dnp() in vn_dict[ref][vn][choice][key_opts()]
                eliminate = False

                if fp_choice_value != None:
                    if fp_value != fp_choice_value:
                        eliminate = True

                # TODO these should only be compared if their checkboxes are checked or the config requests it.

                if use_attr_excl_from_bom():
                    if fp_excl_bom != fp_choice_dnp:
                        eliminate = True

                if use_attr_excl_from_posfiles():
                    if fp_excl_pos != fp_choice_dnp:
                        eliminate = True

                if use_attr_dnp():
                    if fp_dnp != fp_choice_dnp:
                        eliminate = True

                if eliminate: # defer elimination until after iteration
                    eliminate_choices.append(choice)
            
            for choice in eliminate_choices:
                choices[vn].remove(choice)

    # Step 2: Create a dict with candidate Choices.
    selection = {}
    for choice in choices:
        if len(choices[choice]) == 1:
            selection[choice] = choices[choice][0]
        else:
            selection[choice] = ''

    # Step 3: Eliminate candidate Choice that do not exactly match the required conditions.
    #         (Basically, this is a dry-run of the apply function.)
    for ref in vn_dict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        fp_value = fp.GetValue()
        if use_attr_excl_from_bom():
            fp_excl_bom = fp.IsExcludedFromBOM()
        if use_attr_excl_from_posfiles():
            fp_excl_pos = fp.IsExcludedFromPosFiles()
        if use_attr_dnp():
            fp_dnp = fp.IsDNP()
        for vn in vn_dict[ref]:
            selected_choice = selection[vn]
            if selected_choice != '':
                new_value = vn_dict[ref][vn][selected_choice][key_val()]
                new_dnp = opt_dnp() in vn_dict[ref][vn][selected_choice][key_opts()]
                mismatch = False
                if new_value != None:
                    if fp_value != new_value:
                        mismatch = True
                if use_attr_excl_from_bom():
                    if fp_excl_bom != new_dnp:
                        mismatch = True
                if use_attr_excl_from_posfiles():
                    if fp_excl_pos != new_dnp:
                        mismatch = True
                if use_attr_dnp():
                    if fp_dnp != new_dnp:
                        mismatch = True
                if mismatch:
                    selection[vn] = ''

    return selection

def apply_choices(board, vn_dict, selection, dry_run = False):
    changes = []

    for ref in vn_dict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        for vn in vn_dict[ref]:
            selected_choice = selection[vn]
            if selected_choice != '': # None?
                vn_text = f'{vn}.{selected_choice}'
                new_value = vn_dict[ref][vn][selected_choice][key_val()]
                if new_value != None:
                    old_value = fp.GetValue()
                    if old_value != new_value:
                        changes.append(f"Change {ref} value from '{old_value}' to '{new_value}' ({vn_text}).")
                        if not dry_run:
                            fp.SetValue(new_value)
                new_dnp = opt_dnp() in vn_dict[ref][vn][selected_choice][key_opts()]
                if use_attr_dnp():
                    old_dnp = fp.IsDNP()
                    if old_dnp != new_dnp:
                        changes.append(f"Change {ref} 'Do not populate' from '{bool_as_text(old_dnp)}' to '{bool_as_text(new_dnp)}' ({vn_text}).")
                        if not dry_run:
                            fp.SetDNP(new_dnp)
                if use_attr_excl_from_bom():
                    old_excl_from_bom = fp.IsExcludedFromBOM()
                    if old_excl_from_bom != new_dnp:
                        changes.append(f"Change {ref} 'Exclude from bill of materials' from '{bool_as_text(old_excl_from_bom)}' to '{bool_as_text(new_dnp)}' ({vn_text}).")
                        if not dry_run:
                            fp.SetExcludedFromBOM(new_dnp)
                if use_attr_excl_from_posfiles():
                    old_excl_from_posfiles = fp.IsExcludedFromPosFiles()
                    if old_excl_from_posfiles != new_dnp:
                        changes.append(f"Change {ref} 'Exclude from position files' from '{bool_as_text(old_excl_from_posfiles)}' to '{bool_as_text(new_dnp)}' ({vn_text}).")
                        if not dry_run:
                            fp.SetExcludedFromPosFiles(new_dnp)
    return changes

def get_vn_dict(board):
    vns = {}
    errors = []
    fps = board.GetFootprints()
    fps.sort(key=lambda x: x.GetReference())
    accepted_options = [opt_dnp()]

    vn_field_name = variant_cfg_field_name()

    for fp in fps:
        ref = fp.GetReference()
        if wrap_HasField(fp, vn_field_name):
            if ref in vns:
                errors.append(f"{ref}: Multiple footprints with same reference containing a rule definition field '{vn_field_name}'.")
                continue

            vns[ref] = {}
            field_value = wrap_GetField(fp, vn_field_name)
            if len(field_value) < 1:
                # field exists, but is empty. ignore it.
                # a field containing only white-space is considered an error.
                continue

            try:
                vn_def = split_ruledef(field_value, ',', False)
            except Exception as e:
                errors.append(f"{ref}: Rule parser error: {str(e)}.")
                continue

            if len(vn_def) < 2:
                errors.append(f"{ref}: Invalid number of elements in rule definition field '{vn_field_name}'.")
                continue

            section_is_vn = True
            for section in vn_def:
                if section_is_vn:
                    # First rule section contains the Vn name only.
                    # TODO clarify rules for Vn name (forbidden characters: "*" ".")
                    try:
                        parts = split_ruledef(section, ' ', True)
                    except Exception as e:
                        errors.append(f"{ref}: Variation name parser error: {str(e)}.")
                        continue
                    if len(parts) != 1:
                        errors.append(f"{ref}: Variation name is not exactly one word.")
                        continue
                    vn = cook_raw_string(parts[0])
                    if not vn in vns[ref]:
                        vns[ref][vn] = {}
                    section_is_vn = False
                else:
                    # Any following rule sections are Vn Choice definitions.
                    try:
                        parts = split_ruledef(section, ':', False)
                    except Exception as e:
                        errors.append(f"{ref}: Choice parser error: {str(e)}.")
                        continue

                    if len(parts) == 0:
                        errors.append(f"{ref}: Empty choice definition.")
                        continue
                    elif len(parts) > 2:
                        errors.append(f"{ref}: Choice definition has more than two parts.")
                        continue

                    if len(parts) == 1: # default choice definition
                        args_part_idx = 0
                        choice_list = [key_default()]
                    else:
                        args_part_idx = 1
                        try:
                            choice_list = split_ruledef(parts[0], ' ', True)
                        except Exception as e:
                            errors.append(f"{ref}: Choice names parser error: {str(e)}.")
                            continue

                    try:
                        raw_args = split_ruledef(parts[args_part_idx], ' ', True)
                    except Exception as e:
                        errors.append(f"{ref}: Choice arguments parser error: {str(e)}.")
                        continue

                    choices = []
                    for choice_name in choice_list:
                        choices.append(cook_raw_string(choice_name))
                    
                    values = []
                    options = []
                    for raw_arg in raw_args:
                        # TODO 'try/except', or is string safe after above processing?
                        arg = cook_raw_string(raw_arg)
                        if raw_arg.startswith('-'): # not supposed to match if arg starts with '\-' or '"-'
                            option = arg[1:]
                            if not option in accepted_options:
                                errors.append(f"{ref}: Unknown or invalid option '{option}'.")
                                continue
                            options.append(option)
                        else:
                            values.append(arg)

                    if len(values) > 1:
                        errors.append(f"{ref}: More than one value assigned inside a choice definition.") # TODO add info in which choice def (index value)
                        continue
                    else:
                        for choice in choices:
                            if choice in vns[ref][vn]:
                                if len(parts) == 1:
                                    errors.append(f"{ref}: Rule contains more than one default choice definition.")
                                else:
                                    errors.append(f"{ref}: Choice '{choice}' is defined more than once inside the rule definition.")
                                continue
                            vns[ref][vn][choice] = {}
                            vns[ref][vn][choice][key_val()] = values[0] if len(values) > 0 else None
                            vns[ref][vn][choice][key_opts()] = options

    if len(vns) == 0:
        errors.append('No rule definitions found.')
        errors.append('')
        errors.append('Please read the documentation to learn how to assign variation rules to symbols/footprints:')
        errors.append(help_url())
    else:
        # Now check that each choice of each variation is defined for each reference.
        # Also, flatten the dict, i.e. assign default values and options to specific choices.
        choices = get_choice_dict(vns)
        for ref in vns:
            for vn in vns[ref]:
                choices_with_value_defined = 0
                for choice in choices[vn]:
                    if choice in vns[ref][vn]: # TODO check that each choice is contained exactly ONCE in vns!
                        if vns[ref][vn][choice][key_val()] == None:
                            # There is a specific choice definition, but it does not contain a value.
                            # Take the value from the default choice (if it exists), keep the options
                            # as defined in the specific choice definition.
                            if key_default() in vns[ref][vn]:
                                vns[ref][vn][choice][key_val()] = vns[ref][vn][key_default()][key_val()]
                    else:
                        # The specific choice definition is missing. Copy value and options from default
                        # choice definition (if it exists).
                        if key_default() in vns[ref][vn]:
                            vns[ref][vn][choice] = {}
                            vns[ref][vn][choice][key_val()] = vns[ref][vn][key_default()][key_val()]
                            vns[ref][vn][choice][key_opts()] = vns[ref][vn][key_default()][key_opts()]
                        else:
                            vns[ref][vn][choice] = {}
                            vns[ref][vn][choice][key_val()] = None
                            vns[ref][vn][choice][key_opts()] = []

                    if vns[ref][vn][choice][key_val()] != None:
                        choices_with_value_defined += 1

                if not (choices_with_value_defined == 0 or choices_with_value_defined == len(choices[vn])):
                    errors.append(f"{ref}: Rule mixes choices with defined ({choices_with_value_defined}) and undefined ({len(choices[vn]) - choices_with_value_defined}) values (either all or none must be defined).")
                    continue

                vns[ref][vn].pop(key_default(), None) # clean-up temporary data: remove default choice data

    return vns, errors

def get_choice_dict(vn_dict):
    choices = {}

    for ref in vn_dict:
        for vn in vn_dict[ref]:
            if not vn in choices:
                choices[vn] = []
            for choice in vn_dict[ref][vn]:
                # In case the input dict still contains temporary data (such as default data), ignore it.
                if choice != key_default() and not choice in choices[vn]:
                    choices[vn].append(choice)

    return choices

def split_ruledef(str, sep, multisep):
    result = []
    item = []
    escaped = False
    quoted = False
    for c in str:
        if escaped:
            item.append(c)
            escaped = False
        elif c == '\\':
            item.append(c)
            escaped = True
        elif c == "'":
            item.append(c)
            quoted = not quoted
        elif c == sep and not quoted:
            if not multisep or len(item) > 0:
                result.append(''.join(item))
                item = []
        else:
            item.append(c)
    if not multisep or len(item) > 0:
        result.append(''.join(item))
    if quoted:
        raise ValueError('Unmatched quote character in string')
    if escaped:
        raise ValueError('Unterminated escape sequence at end of string')

    return result

def cook_raw_string(str):
    result = []
    escaped = False
    quoted = False
    for c in str:
        if escaped:
            result.append(c)
            escaped = False
        elif c == '\\':
            escaped = True
        elif c == "'":
            quoted = not quoted
        else:
            result.append(c)
    if quoted:
        raise ValueError('Unmatched quote character in string')
    if escaped:
        raise ValueError('Unterminated escape sequence at end of string')

    return ''.join(result)

def ShowVariantDialog(board, vn_dict):
    dlg = VariantDialog(board, vn_dict)
    dlg.ShowModal()

class VariantDialog(wx.Dialog):
    def __init__(self, board, vn_dict):
        super(VariantDialog, self).__init__(pcbnew_parent_window(), title=f'KiVar {version()}: Variant Selection', style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.board = board
        self.vn_dict = vn_dict
        choice_dict = get_choice_dict(self.vn_dict)
        preselect = detect_current_choices(self.board, self.vn_dict)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Selections
#        sel_grid = wx.GridSizer(cols=2, hgap=10, vgap=6)
        sel_grid = wx.GridSizer(cols=1, hgap=10, vgap=6)

        # left: variations
        var_box = wx.StaticBox(self, label='Variation Choices')
        var_box_sizer = wx.StaticBoxSizer(var_box)
        var_grid = wx.GridSizer(cols=2, hgap=10, vgap=6)

        self.choices = {}
        for cfg in sorted(choice_dict):
            opts = ['<unset>']
            sorted_choices = sorted(choice_dict[cfg])
            opts.extend(sorted_choices)
            self.choices[cfg] = wx.Choice(self, choices=opts)
            sel_opt = preselect[cfg]
            sel_index = 0 # <unset> by default
            if sel_opt != '':
                sel_index = sorted_choices.index(sel_opt) + 1
            self.choices[cfg].SetSelection(sel_index)
            self.choices[cfg].Bind(wx.EVT_CHOICE, self.on_change)
            
            var_grid.Add(wx.StaticText(self, label=f'{cfg}:'), 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
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
        # opt_box_sizer.Add(reset_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 4)
        # opt_box_sizer.Add(wx.StaticText(self, label=''), 1, wx.EXPAND | wx.ALL)
        # sel_grid.Add(opt_box_sizer, 0, wx.EXPAND | wx.ALL, 4)

        sizer.Add(sel_grid, 0, wx.EXPAND | wx.ALL, 4)

        # Changes Text
        changes_box = wx.StaticBox(self, label='Changes To Be Applied')
        self.changes_box_sizer = wx.StaticBoxSizer(changes_box)
        self.changes_box_sizer.SetMinSize((640, 280))

        self.changes_text_win = wx.ScrolledWindow(self, wx.ID_ANY)
        self.changes_text = wx.TextCtrl(self.changes_text_win, wx.ID_ANY, style=wx.BORDER_NONE | wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.update_text()

        text_sizer = wx.BoxSizer(wx.VERTICAL)
        text_sizer.Add(self.changes_text, 1, wx.EXPAND | wx.ALL, 3)

        self.changes_text_win.SetSizer(text_sizer)
        self.changes_box_sizer.Add(self.changes_text_win, 1, wx.EXPAND | wx.ALL)

        sizer.Add(self.changes_box_sizer, 1, wx.EXPAND | wx.ALL, 8)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        ok_button = wx.Button(self, label='Update PCB')
#        update_button = wx.Button(self, label='Reset Choices')
        cancel_button = wx.Button(self, label='Close')

        button_sizer.Add(cancel_button, 0, wx.ALL, 8)
#        button_sizer.Add(update_button, 0, wx.ALL, 8)
        button_sizer.Add(ok_button, 0, wx.ALL, 8)

        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT)

        self.SetSizerAndFit(sizer)
        # TODO avoid 50/50 split between boxes. should be dynamic!

        self.Fit()
        self.CenterOnParent()

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
        apply_choices(self.board, self.vn_dict, self.selections())
        pcbnew.Refresh()
        self.Destroy()

    def on_change(self, event):
        self.update_text()

#    def on_update(self, event):
#        self.update_text()

    def on_cancel(self, event):
        self.Destroy()

    def update_text(self):
        changes = apply_choices(self.board, self.vn_dict, self.selections(), True)
        change_text = '\n'.join(changes)
        self.changes_text.SetValue(change_text)

def ShowErrorDialog(title, errors):
    dialog = TextDialog(f'KiVar {version()}: {title}', '\n'.join(errors))
    dialog.ShowModal()
    dialog.Destroy()

class TextDialog(wx.Dialog):
    def __init__(self, title, text):
        super(TextDialog, self).__init__(pcbnew_parent_window(), title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, size=(800, 500))

        text_win = wx.ScrolledWindow(self, wx.ID_ANY)
        self.text = wx.TextCtrl(text_win, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.text.SetValue(text)

        scr_win_sizer = wx.BoxSizer(wx.VERTICAL)
        scr_win_sizer.Add(self.text, 1, wx.EXPAND | wx.ALL)
        text_win.SetSizer(scr_win_sizer)

        self.ok_button = wx.Button(self, wx.ID_OK, 'Dismiss')
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.ok_button, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text_win, 1, wx.EXPAND | wx.ALL, 8)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL)
        self.SetSizer(sizer)

        self.ok_button.SetFocus()

VariantPlugin().register()
