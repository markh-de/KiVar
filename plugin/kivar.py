import pcbnew
import wx
import wx.lib.agw.hyperlink as hyperlink
from os import path as os_path

# Used abbreviations:
# * Vn = Variation
# * Ch = Choice

# TODO:
#
# * Add a Setup plugin (separate button) that defines DNP->NoPos/NoBom behavior. Having this in a separate dialog (which
#   also takes care of nonvolatile storage of the settings) removes any dynamic reload/refresh requirements.
#   (Setup plugin shall have similar icon with wrench in the foreground.)
#
# * Setup plugin: Save option settings as some object in PCB (board variables or text box)
#
# * After applying configuration, define board variables containing the choice for each vn, e.g. ${KIVAR.BOOT_SEL} => NAND
#   (requires KiCad API change/fix: https://gitlab.com/kicad/code/kicad/-/issues/16426)
#

class VariantPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'KiVar'
        self.category = 'Assembly Variants'
        self.description = 'Switches predefined assembly variant choices'
        self.icon_file_name = os_path.join(os_path.dirname(__file__), 'kivar-icon-light.svg')
        self.dark_icon_file_name = os_path.join(os_path.dirname(__file__), 'kivar-icon-dark.svg')

    def Run(self):
        board = pcbnew.GetBoard()
        vn_dict, errors = get_vn_dict(board)
        if len(errors) > 0:
            ShowErrorDialog('Rule errors', errors, board)
        elif len(vn_dict) == 0:
            ShowMissingRulesDialog()
        else:
            ShowVariantDialog(board, vn_dict)

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

def wrap_FocusOnItem(item):
    if pcbnew_version() >= 799:
        return pcbnew.FocusOnItem(item)
    # not supported on earlier versions

def pcbnew_version():
    return int(pcbnew.GetMajorMinorPatchVersion().split('.')[0]) * 100 + int(pcbnew.GetMajorMinorPatchVersion().split('.')[1])

def pcbnew_parent_window():
    return wx.FindWindowByName('PcbFrame')

def version():
    return '0.1.0'

def variant_cfg_field_name():
    return 'KiVar.Rule'

def help_url():
    return 'https://github.com/markh-de/KiVar#usage'

def opt_unfit():
    return '!'

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

def natural_sort_key(str):
    key = []
    part = ''
    for c in str:
        if c.isdigit():
            part += c
        else:
            if part:
                key.append((0, int(part), ''))
                part = ''
            key.append((1, 0, c.lower()))
    if part:
        key.append((0, int(part), ''))
    return key

def escape_string_if_required(str):
    if any(c in str for c in (',', ' ', '-', '\\', '(', ')')):
        result = "'"
        for c in str:
            if c == '\\' or c == "'":
                result += '\\'
            result += c
        result += "'"
    else:
        result = str
    return result

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
                fp_choice_unfit = opt_unfit() in vn_dict[ref][vn][choice][key_opts()]
                eliminate = False

                if fp_choice_value is not None:
                    if fp_value != fp_choice_value:
                        eliminate = True

                # TODO these should only be compared if their checkboxes are checked or the config requests it.

                if use_attr_excl_from_bom():
                    if fp_excl_bom != fp_choice_unfit:
                        eliminate = True

                if use_attr_excl_from_posfiles():
                    if fp_excl_pos != fp_choice_unfit:
                        eliminate = True

                if use_attr_dnp():
                    if fp_dnp != fp_choice_unfit:
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
                new_unfit = opt_unfit() in vn_dict[ref][vn][selected_choice][key_opts()]
                mismatch = False
                if new_value is not None:
                    if fp_value != new_value:
                        mismatch = True
                if use_attr_excl_from_bom():
                    if fp_excl_bom != new_unfit:
                        mismatch = True
                if use_attr_excl_from_posfiles():
                    if fp_excl_pos != new_unfit:
                        mismatch = True
                if use_attr_dnp():
                    if fp_dnp != new_unfit:
                        mismatch = True
                if mismatch:
                    selection[vn] = ''

    return selection

# TODO check each '' or "" and use None, if applicable

def apply_choices(board, vn_dict, selection, dry_run = False):
    changes = []

    for ref in vn_dict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        for vn in vn_dict[ref]:
            selected_choice = selection[vn]
            if selected_choice != '': # None?
                choice_text = f'{escape_string_if_required(vn)}.{escape_string_if_required(selected_choice)}'
                new_value = vn_dict[ref][vn][selected_choice][key_val()]
                if new_value is not None:
                    old_value = fp.GetValue()
                    if old_value != new_value:
                        changes.append([ref, f"Change {ref} value from '{old_value}' to '{new_value}' ({choice_text})."])
                        if not dry_run:
                            fp.SetValue(new_value)
                new_unfit = opt_unfit() in vn_dict[ref][vn][selected_choice][key_opts()]
                if use_attr_dnp():
                    old_dnp = fp.IsDNP()
                    if old_dnp != new_unfit:
                        changes.append([ref, f"Change {ref} 'Do not populate' from '{bool_as_text(old_dnp)}' to '{bool_as_text(new_unfit)}' ({choice_text})."])
                        if not dry_run:
                            fp.SetDNP(new_unfit)
                if use_attr_excl_from_bom():
                    old_excl_from_bom = fp.IsExcludedFromBOM()
                    if old_excl_from_bom != new_unfit:
                        changes.append([ref, f"Change {ref} 'Exclude from bill of materials' from '{bool_as_text(old_excl_from_bom)}' to '{bool_as_text(new_unfit)}' ({choice_text})."])
                        if not dry_run:
                            fp.SetExcludedFromBOM(new_unfit)
                if use_attr_excl_from_posfiles():
                    old_excl_from_posfiles = fp.IsExcludedFromPosFiles()
                    if old_excl_from_posfiles != new_unfit:
                        changes.append([ref, f"Change {ref} 'Exclude from position files' from '{bool_as_text(old_excl_from_posfiles)}' to '{bool_as_text(new_unfit)}' ({choice_text})."])
                        if not dry_run:
                            fp.SetExcludedFromPosFiles(new_unfit)
    return changes

def get_vn_dict(board):
    vns = {}
    errors = []
    fps = board.GetFootprints()
    fps.sort(key=lambda x: natural_sort_key(x.GetReference()))
    accepted_options = [opt_unfit()]

    vn_field_name = variant_cfg_field_name()

    for fp in fps:
        ref = fp.GetReference()
        if wrap_HasField(fp, vn_field_name):
            if ref in vns:
                errors.append([ref, f"{ref}: Multiple footprints with same reference containing a rule definition field '{vn_field_name}'."])
                continue

            field_value = wrap_GetField(fp, vn_field_name)
            if len(field_value) < 1:
                # field exists, but is empty. ignore it.
                # a field containing only white-space is considered an error.
                continue

            vns[ref] = {}
            try:
                vn_defs = split_raw_str(field_value, ' ', True)
            except Exception as e:
                errors.append([ref, f"{ref}: Rule splitter error: {str(e)}."])
                continue

            if len(vn_defs) < 2:
                errors.append([ref, f"{ref}: Invalid number of elements in rule definition field '{vn_field_name}'."])
                continue

            section_is_vn = True
            vn = None
            for section in vn_defs:
                try:
                    name, content = split_choice(section)
                except Exception as e:
                    errors.append([ref, f"{ref}: Section splitter error: {str(e)}."])
                    continue

                if section_is_vn:
                    # First rule section contains the Vn name only.
                    # TODO clarify rules for Vn name (forbidden characters: "*" ".")
                    section_is_vn = False
                    cooked_name = cook_raw_string(name)
                    if cooked_name is None or cooked_name == '':
                        errors.append([ref, f"{ref}: Variation aspect name must not be empty."])
                        continue
                    if content is not None:
                        errors.append([ref, f"{ref}: First rule section must be variation name without parenthesis."])
                        continue
                    vn = cooked_name
                    if not vn in vns[ref]:
                        vns[ref][vn] = {}
                elif vn is not None:
                    # Any following rule sections are Vn Choice definitions.
                    if name is None or name == '':
                        errors.append([ref, f"{ref}: Variation choice name list must not be empty."])
                        continue
                    if content is None:
                        errors.append([ref, f"{ref}: Variation choice definition must have parenthesis."])
                        continue

                    try:
                        raw_names = split_raw_str(name, ',', False)
                    except Exception as e:
                        errors.append([ref, f"{ref}: Choice names splitter error: {str(e)}."])
                        continue

                    try:
                        raw_args = split_raw_str(content, ' ', True)
                    except Exception as e:
                        errors.append([ref, f"{ref}: Choice arguments splitter error: {str(e)}."])
                        continue

                    choices = []
                    for choice_name in raw_names:
                        cooked_name = cook_raw_string(choice_name)
                        if cooked_name == '':
                            errors.append([ref, f"{ref}: Variation choice name must not be empty."])
                            continue
                        choices.append(cooked_name)
                    
                    values = []
                    options = []
                    for raw_arg in raw_args:
                        # TODO 'try/except', or is string safe after above processing?
                        arg = cook_raw_string(raw_arg)
                        if raw_arg.startswith('-'): # not supposed to match if arg starts with \- or '-'
                            option = arg[1:]
                            if not option in accepted_options:
                                errors.append([ref, f"{ref}: Unknown or invalid option '{option}'."])
                                continue
                            options.append(option)
                        else:
                            values.append(arg)

                    if len(values) > 1:
                        errors.append([ref, f"{ref}: More than one value provided inside a choice definition."]) # TODO add info in which choice def (index value)
                        continue
                    else:
                        for choice in choices:
                            if choice in vns[ref][vn]:
                                errors.append([ref, f"{ref}: Choice '{choice}' is defined more than once inside the rule definition."])
                                continue
                            vns[ref][vn][choice] = {}
                            vns[ref][vn][choice][key_val()] = values[0] if len(values) > 0 else None
                            vns[ref][vn][choice][key_opts()] = options

    # Now check that each choice of each variation is defined for each reference.
    # Also, flatten the dict, i.e. assign default values and options to specific choices.
    choices = get_choice_dict(vns)
    for ref in vns:
        for vn in vns[ref]:
            choices_with_value_defined = 0
            for choice in choices[vn]:
                if choice in vns[ref][vn]: # TODO check that each choice is contained exactly ONCE in vns!
                    if vns[ref][vn][choice][key_val()] is None:
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

                if vns[ref][vn][choice][key_val()] is not None:
                    choices_with_value_defined += 1

            if not (choices_with_value_defined == 0 or choices_with_value_defined == len(choices[vn])):
                errors.append([ref, f"{ref}: Rule mixes choices with defined ({choices_with_value_defined}) and undefined ({len(choices[vn]) - choices_with_value_defined}) values (either all or none must be defined)."])
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

def split_choice(str):
    item = []
    outside = None
    inside = None
    escaped = False
    quoted = False
    parens = 0
    end_expected = False
    for c in str:
        if end_expected:
            raise ValueError('String extends beyond closing parenthesis')
        elif escaped:
            escaped = False
            item.append(c)
        elif c == '\\':
            escaped = True
            item.append(c)
        elif c == "'":
            quoted = not quoted
            item.append(c)
        elif c == '(' and not quoted:
            parens += 1
            if parens == 1:
                outside = ''.join(item)
                inside = '' # inside: no parens -> None, empty parens -> ''
                item = []
            else:
                item.append(c)
        elif c == ')' and not quoted:
            if parens > 0:
                parens -= 1
                if parens == 0:
                    inside = ''.join(item)
                    item = []
                    end_expected = True
                else:
                    item.append(c)
            else:
                raise ValueError('Unmatched closing parenthesis')
        else:
            item.append(c)
    if parens > 0:
        raise ValueError('Unmatched opening parenthesis')
    if quoted:
        raise ValueError('Unmatched quote character in string')
    if escaped:
        raise ValueError('Unterminated escape sequence at end of string')
    if len(item) > 0:
        outside = ''.join(item)

    return outside, inside

def split_raw_str(str, sep, multisep):
    result = []
    item = []
    escaped = False
    quoted = False
    parens = 0
    for c in str:
        if escaped:
            escaped = False
            item.append(c)
        elif c == '\\':
            escaped = True
            item.append(c)
        elif c == "'":
            quoted = not quoted
            item.append(c)
        elif c == '(' and not quoted:
            parens += 1
            item.append(c)
        elif c == ')' and not quoted:
            if parens > 0:
                parens -= 1
            else:
                raise ValueError('Unmatched closing parenthesis')
            item.append(c)
        elif c == sep and not quoted and parens == 0:
            if not multisep or len(item) > 0:
                result.append(''.join(item))
                item = []
        else:
            item.append(c)
    if parens > 0:
        raise ValueError('Unmatched opening parenthesis')
    if quoted:
        raise ValueError('Unmatched quote character in string')
    if escaped:
        raise ValueError('Unterminated escape sequence at end of string')
    if not multisep or len(item) > 0:
        result.append(''.join(item))

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
        super().__init__(pcbnew_parent_window(), title=f'KiVar {version()}: Variant Selection', style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

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
        for cfg in sorted(choice_dict, key=natural_sort_key):
            opts = ['<unset>']
            sorted_choices = sorted(choice_dict[cfg], key=natural_sort_key)
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
        apply_choices(self.board, self.vn_dict, self.selections())
        pcbnew.Refresh()
        self.Destroy()

    def on_change(self, event):
        self.update_list()

#    def on_update(self, event):
#        self.update_text()

    def on_cancel(self, event):
        self.Destroy()

    def update_list(self):
        changes = apply_choices(self.board, self.vn_dict, self.selections(), True)
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
