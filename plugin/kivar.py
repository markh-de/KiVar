import pcbnew

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

def version():
    return '0.2.0-dev1'

def variant_cfg_field_name():
    return 'KiVar.Rule'

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
    if any(c in str for c in ', -\\()='):
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
                choice_text = f'{escape_string_if_required(vn)}={escape_string_if_required(selected_choice)}'
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
