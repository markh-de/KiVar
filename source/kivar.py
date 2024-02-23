import pcbnew

def version():
    return '0.2.0-dev2'

def pcbnew_version():
    v = pcbnew.GetMajorMinorPatchVersion().split('.')
    return int(v[0]) * 100 + int(v[1])

def get_fp_fields(fp):
    if pcbnew_version() < 799:
        fields = fp.GetProperties()
    else:
        fields = fp.GetFieldsText()
    return fields

def get_my_fp_fields(fp):
    result = {}
    prefix = fp_field_prefix().lower()
    fields = get_fp_fields(fp)
    for field in fields:
        lc_field = field.lower()
        if lc_field.startswith(prefix):
            result[lc_field[len(prefix):]] = fields[field]
    return result

def fp_field_prefix():
    return 'kivar.'

def field_suffix_rule():
    return 'rule' # must be lower-case

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

def detect_current_choices(board, vardict):
    choices = get_choice_dict(vardict)

    # How it works:
    # We start with the usual Choice dict filled with all possible Choices per Aspect.
    # Then we eliminate all Choices whose values do not match the actual FP values (or attributes).
    # If exactly one Choice per Aspect remains, then we convert these to a selection dict, which is then
    # filtered to contain only Choices that exactly match the actual FP values and attributes.

    # Step 1: Eliminate Choices not matching the actual FP values.
    for ref in vardict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        fp_value = fp.GetValue()

        if use_attr_excl_from_bom():
            fp_excl_bom = fp.IsExcludedFromBOM()
        if use_attr_excl_from_posfiles():
            fp_excl_pos = fp.IsExcludedFromPosFiles()
        if use_attr_dnp():
            fp_dnp = fp.IsDNP()

        for aspect in vardict[ref]:
            # Check each remaining Choice whether it can be eliminated.
            eliminate_choices = []
            for choice in choices[aspect]:
                fp_choice_value = vardict[ref][aspect][choice][key_val()]
                fp_choice_unfit = opt_unfit() in vardict[ref][aspect][choice][key_opts()]
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
                choices[aspect].remove(choice)

    # Step 2: Create a dict with candidate Choices.
    selection = {}
    for choice in choices:
        if len(choices[choice]) == 1:
            selection[choice] = choices[choice][0]
        else:
            selection[choice] = None

    # Step 3: Eliminate candidate Choice that do not exactly match the required conditions.
    #         (Basically, this is a dry-run of the apply function.)
    for ref in vardict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        fp_value = fp.GetValue()
        if use_attr_excl_from_bom():
            fp_excl_bom = fp.IsExcludedFromBOM()
        if use_attr_excl_from_posfiles():
            fp_excl_pos = fp.IsExcludedFromPosFiles()
        if use_attr_dnp():
            fp_dnp = fp.IsDNP()
        for aspect in vardict[ref]:
            selected_choice = selection[aspect]
            if selected_choice is not None:
                new_value = vardict[ref][aspect][selected_choice][key_val()]
                new_unfit = opt_unfit() in vardict[ref][aspect][selected_choice][key_opts()]
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
                    selection[aspect] = None

    return selection

def apply_choices(board, vardict, selection, dry_run = False):
    changes = []

    for ref in vardict:
        fp = board.FindFootprintByReference(ref) # TODO error handling! can return "None"
        for aspect in vardict[ref]:
            selected_choice = selection[aspect]
            if selected_choice is not None:
                choice_text = f'{escape_string_if_required(aspect)}={escape_string_if_required(selected_choice)}'
                new_value = vardict[ref][aspect][selected_choice][key_val()]
                if new_value is not None:
                    old_value = fp.GetValue()
                    if old_value != new_value:
                        changes.append([ref, f"Change {ref} value from '{old_value}' to '{new_value}' ({choice_text})."])
                        if not dry_run:
                            fp.SetValue(new_value)
                new_unfit = opt_unfit() in vardict[ref][aspect][selected_choice][key_opts()]
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

def get_vardict(board):
    vardict = {}
    errors = []
    fps = board.GetFootprints()
    fps.sort(key=lambda x: natural_sort_key(x.GetReference()))
    accepted_options = [opt_unfit()]

    rule_field = field_suffix_rule()

    for fp in fps:
        ref = fp.GetReference()
        fields = get_my_fp_fields(fp)
        if field_suffix_rule() in fields:
            if ref in vardict:
                errors.append([ref, f"{ref}: Multiple footprints with same reference containing a rule definition field '{rule_field}'."])
                continue

            field_value = fields[field_suffix_rule()]
            if len(field_value) < 1:
                # field exists, but is empty. ignore it.
                # a field containing only white-space is considered an error.
                continue

            vardict[ref] = {}
            try:
                rule_sections = split_raw_str(field_value, ' ', True)
            except Exception as e:
                errors.append([ref, f"{ref}: Rule splitter error: {str(e)}."])
                continue

            if len(rule_sections) < 2:
                errors.append([ref, f"{ref}: Invalid number of elements in rule definition field '{rule_field}'."])
                continue

            section_is_aspect_name = True
            aspect = None
            for section in rule_sections:
                try:
                    name, content = split_choice(section)
                except Exception as e:
                    errors.append([ref, f"{ref}: Section splitter error: {str(e)}."])
                    continue

                if section_is_aspect_name:
                    # First rule section contains the Aspect name only.
                    # TODO clarify rules for Aspect name (forbidden characters: "*" ".")
                    section_is_aspect_name = False
                    cooked_name = cook_raw_string(name)
                    if cooked_name is None or cooked_name == '':
                        errors.append([ref, f"{ref}: Variation aspect name must not be empty."])
                        continue
                    if content is not None:
                        errors.append([ref, f"{ref}: First rule section must be variation name without parenthesis."])
                        continue
                    aspect = cooked_name
                    if not aspect in vardict[ref]:
                        vardict[ref][aspect] = {}
                elif aspect is not None:
                    # Any following rule sections are Choice definitions.
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
                            if choice in vardict[ref][aspect]:
                                errors.append([ref, f"{ref}: Choice '{choice}' is defined more than once inside the rule definition."])
                                continue
                            vardict[ref][aspect][choice] = {}
                            vardict[ref][aspect][choice][key_val()] = values[0] if len(values) > 0 else None
                            vardict[ref][aspect][choice][key_opts()] = options

    # Now check that each Choice of each Aspect is defined for each reference.
    # Also, flatten the dict, i.e. assign default values and options to specific Choices.
    choices = get_choice_dict(vardict)
    for ref in vardict:
        for aspect in vardict[ref]:
            choices_with_value_defined = 0
            for choice in choices[aspect]:
                if choice in vardict[ref][aspect]: # TODO check that each Choice is contained exactly ONCE!
                    if vardict[ref][aspect][choice][key_val()] is None:
                        # There is a specific Choice definition, but it does not contain a value.
                        # Take the value from the Default Choice (if it exists), keep the options
                        # as defined in the specific Choice definition.
                        if key_default() in vardict[ref][aspect]:
                            vardict[ref][aspect][choice][key_val()] = vardict[ref][aspect][key_default()][key_val()]
                else:
                    # The specific Choice definition is missing. Copy value and options from Default
                    # Choice definition (if it exists).
                    if key_default() in vardict[ref][aspect]:
                        vardict[ref][aspect][choice] = {}
                        vardict[ref][aspect][choice][key_val()] = vardict[ref][aspect][key_default()][key_val()]
                        vardict[ref][aspect][choice][key_opts()] = vardict[ref][aspect][key_default()][key_opts()]
                    else:
                        vardict[ref][aspect][choice] = {}
                        vardict[ref][aspect][choice][key_val()] = None
                        vardict[ref][aspect][choice][key_opts()] = []

                if vardict[ref][aspect][choice][key_val()] is not None:
                    choices_with_value_defined += 1

            if not (choices_with_value_defined == 0 or choices_with_value_defined == len(choices[aspect])):
                errors.append([ref, f"{ref}: Rule mixes choices with defined ({choices_with_value_defined}) and undefined ({len(choices[aspect]) - choices_with_value_defined}) values (either all or none must be defined)."])
                continue

            vardict[ref][aspect].pop(key_default(), None) # clean-up temporary data: remove default Choice data

    return vardict, errors

def get_choice_dict(vardict):
    choices = {}

    for ref in vardict:
        for aspect in vardict[ref]:
            if not aspect in choices:
                choices[aspect] = []
            for choice in vardict[ref][aspect]:
                # In case the input dict still contains temporary data (such as default data), ignore it.
                if choice != key_default() and not choice in choices[aspect]:
                    choices[aspect].append(choice)

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
