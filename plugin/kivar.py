import pcbnew
import wx
from os import path as os_path

# Used abbreviations:
# * Vn = Variation
# * Ch = Choice

# TODO:
#
# * Use a *modal* main dialog, or add a "Refresh and preselect" button, that rebuilds the Vn dict and preselects
#   all choices (may be also useful when checkboxes are added, because preselect criteria depend on these checkbox states).
#
# * After applying configuration, define board variables containing the choice for each vn, e.g. ${KIVAR.BOOT_SEL} => NAND

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
            dialog = VariantDialog(board, vn_dict)
        else:
            dialog = TextDialog('Errors', '\n'.join(errors))
        dialog.Show()

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

def version():
    return '0.0.1'

def variant_cfg_field_name():
    return 'KiVar.Rule'

def help_url():
    return 'https://github.com/markh-de/KiVar'

def opt_dnp():
    return 'dnp'

def key_val():
    return 'v'

def key_vals():
    return 'vl'

def key_opts():
    return 'o'

def key_default():
    return '*'

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

def apply_choices(board, vn_dict, selection):
    changes = []

    for ref in vn_dict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        for vn in vn_dict[ref]:
            selected_choice = selection[vn]
            if selected_choice != '':
                new_value = vn_dict[ref][vn][selected_choice][key_val()]
                new_dnp = opt_dnp() in vn_dict[ref][vn][selected_choice][key_opts()]
                if fp.GetValue() != new_value:
                    changes.append(f"<{vn}.{selected_choice}> {ref}: Value => '{new_value}'")
                    fp.SetValue(new_value)
                if use_attr_excl_from_bom():
                    if fp.IsExcludedFromBOM() != new_dnp:
                        changes.append(f"<{vn}.{selected_choice}> {ref}: Attribute [Exclude from bill of materials] => {new_dnp}")
                        fp.SetExcludedFromBOM(new_dnp)
                if use_attr_excl_from_posfiles():
                    if fp.IsExcludedFromPosFiles() != new_dnp:
                        changes.append(f"<{vn}.{selected_choice}> {ref}: Attribute [Exclude from position files] => {new_dnp}")
                        fp.SetExcludedFromPosFiles(new_dnp)
                if use_attr_dnp():
                    if fp.IsDNP() != new_dnp:
                        changes.append(f"<{vn}.{selected_choice}> {ref}: Attribute [Do not populate] => {new_dnp}")
                        fp.SetDNP(new_dnp)
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
                    elif len(parts) == 1 and len(values) < 1:
                        errors.append(f"{ref}: Default choice does not define a value.") # TODO add info in which choice def (index value)
                        continue
                    else:
                        for choice in choices:
                            if choice in vns[ref][vn]:
                                if len(parts) == 1:
                                    errors.append(f"{ref}: Default choice is defined more than once inside the rule definition.")
                                else:
                                    errors.append(f"{ref}: Choice '{choice}' is defined more than once inside the rule definition.")
                                continue
                            vns[ref][vn][choice] = {}
                            vns[ref][vn][choice][key_vals()] = values
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
                for choice in choices[vn]:
                    if choice in vns[ref][vn]: # TODO check that each choice is contained exactly ONCE in vns!
                        # There is a specific choice definition, but it does not contain a value.
                        # Take the value from the default choice (if it exists), keep the options
                        # as defined in the specific choice definition.
                        if len(vns[ref][vn][choice][key_vals()]) > 0:
                            vns[ref][vn][choice][key_val()] = vns[ref][vn][choice][key_vals()][0]
                        elif key_default() in vns[ref][vn]: # default choice is guaranteed to contain one value
                            vns[ref][vn][choice][key_val()] = vns[ref][vn][key_default()][key_vals()][0]
                        else:
                            errors.append(f"{ref}: No default choice definition available for missing value in definition of choice '{choice}'.")
                            continue
                    else:
                        # The specific choice definition is missing. Copy value and options from default
                        # choice definition (if it exists).
                        if key_default() in vns[ref][vn]: # default choice is guaranteed to contain one value
                            vns[ref][vn][choice] = {}
                            vns[ref][vn][choice][key_val()] = vns[ref][vn][key_default()][key_vals()][0]
                            vns[ref][vn][choice][key_opts()] = vns[ref][vn][key_default()][key_opts()]
                        else:
                            errors.append(f"{ref}: No default choice definition available for missing definition of choice '{choice}'.")
                            continue

                    vns[ref][vn][choice].pop(key_vals(), None) # clean-up temporary data: remove value list from choice
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

class VariantDialog(wx.Dialog):
    def __init__(self, board, vn_dict):
        self.board = board
        self.vn_dict = vn_dict
        choice_dict = get_choice_dict(self.vn_dict)
        preselect = detect_current_choices(self.board, self.vn_dict)

        # TODO can we avoid that the window border appears early?

        wx.Dialog.__init__(self, None, title=f'KiVar {version()} Variant Selection', style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        sizer = wx.BoxSizer(wx.VERTICAL)

        italic = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)

        options_grid = wx.GridSizer(cols=2, hgap=10, vgap=6)

        vn_label = wx.StaticText(self, label='Variation')
        ch_label = wx.StaticText(self, label='Choice')
        vn_label.SetFont(italic)
        ch_label.SetFont(italic)
        options_grid.Add(vn_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)
        options_grid.Add(ch_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)

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
            
            options_grid.Add(wx.StaticText(self, label=f'{cfg}:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
            options_grid.Add(self.choices[cfg], 0, wx.EXPAND)

        sizer.Add(options_grid, 1, wx.EXPAND | wx.ALL, 10)

# TODO use more complex layout:        sizer = wx.GridBagSizer(hgap=5, vgap=5)
# TODO add checkboxes that allow enabling/disabling automatic checking/setting of attribs!

        self.ok_button = wx.Button(self, label='OK')
        self.cancel_button = wx.Button(self, label='Cancel')

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.cancel_button, 0, wx.ALL, 5)
        button_sizer.Add(self.ok_button, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT)

        self.SetSizerAndFit(sizer)

        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

    def on_ok(self, event):
        selections = {}

        for choice in self.choices:
            sel_value = self.choices[choice].GetStringSelection()
            if self.choices[choice].GetSelection() < 1:
                sel_value = '' # <unset>, do not apply to values
            selections[choice] = sel_value

        changes = apply_choices(self.board, self.vn_dict, selections)
        pcbnew.Refresh()
        
        if len(changes) == 0:
            changes = ['No changes.']

        change_text = '\n'.join(changes)

        dialog = TextDialog('Change report', change_text)
        dialog.ShowModal()
        dialog.Destroy()

        self.Destroy()

    def on_cancel(self, event):
        self.Destroy()

class TextDialog(wx.Dialog):
    def __init__(self, title, text):
        wx.Dialog.__init__(self, None, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, size=(800, 500))

        self.window = wx.ScrolledWindow(self, wx.ID_ANY)
        self.text = wx.TextCtrl(self.window, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.text.SetValue(text)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 10)
        self.window.SetSizer(sizer)

        self.ok_button = wx.Button(self, wx.ID_OK, 'OK')
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.ok_button, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(self.window, 1, wx.EXPAND | wx.ALL, 10)
        dialog_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.SetSizer(dialog_sizer)

        self.ok_button.SetFocus()

VariantPlugin().register()
