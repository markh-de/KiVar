import pcbnew

# TODO case-sensitivity concept! where and when do we lower-case names?
#      keep casing intact at least for reporting field names!

# TODO natural sorting when iterating over field names (-> error output sort order)

# TODO filter locked field names (reference, value, footprint (???)) for set AND get!!

# TODO finalize format how to specify main and aux rules

# TODO example project: use updated UVLO_LO/HI from real project

def version():
    return '0.2.0-dev9'

def pcbnew_version():
    v = pcbnew.GetMajorMinorPatchVersion().split('.')
    return int(v[0]) * 100 + int(v[1])

def fp_to_uuid(fp):
    return fp.m_Uuid.AsString()

def uuid_to_fp(board, uuid):
    # TODO type check. if not FOOTPRINT -> return None
    return board.GetItem(pcbnew.KIID(uuid)).Cast()

def get_fp_fields(fp):
    if pcbnew_version() < 799: fields = fp.GetProperties()
    else:                      fields = fp.GetFieldsText()
    return fields

def set_fp_field(fp, field, value):
    if not field.lower() in ['value', 'reference', 'footprint']:
        if pcbnew_version() < 799: fp.SetProperty(field, value)
        else:                      fp.SetField(field, value)

def get_my_fp_fields(fp):
    result = {}
    prefix = 'KiVar.' # lower-case! TODO
    fields = get_fp_fields(fp)
    for field in fields:
        if field.startswith(prefix): result[field[len(prefix):]] = fields[field]
    return result

def get_rule(fields):
    key = 'Rule' # lower-case! TODO
    return fields[key] if key in fields else None

def get_rule_aspect(fields):
    key = 'Rule.Aspect' # lower-case! TODO
    return fields[key] if key in fields else None

# TODO we should use our split function. at least for aux fields we need to be able to allow special characters (space, period, ...)
#      rework this field reading stuff.

def get_aux(fields):
    result = {}
    prefix = 'Aux.' # lower-case! TODO
    for f in fields:
        if f.startswith(prefix):
            # TODO check for invalid characters in referenced field name (period, etc.)
            result[f[len(prefix):]] = fields[f]
    return result

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
        if c.isdigit(): part += c
        else:
            if part:
                key.append((0, int(part), ''))
                part = ''
            key.append((1, 0, c.lower()))
    if part: key.append((0, int(part), ''))
    return key

def escape_str(str):
    result = ''
    for c in str:
        if c == '\\' or c == "'": result += '\\'
        result += c
    return result

def quote_str(str):
    if str == '': result = "''"
    else:
        if any(c in str for c in ', -\\()='):
            result = "'"
            for c in str:
                if c == '\\' or c == "'": result += '\\'
                result += c
            result += "'"
        else: result = str
    return result

def key_aspect():  return 'a'
def key_main():    return 'd'
def key_aux():     return 'x'
def key_default(): return '*'
def key_value():   return 'v'
def key_options(): return 'o'
def opt_unfit():   return '!'

def detect_current_choices(board, vardict):
    choices = get_choice_dict(vardict)

    # How it works:
    # We start with the usual Choice dict filled with all possible Choices per Aspect.
    # Then we eliminate all Choices whose values do not match the actual FP values (or attributes).
    # If exactly one Choice per Aspect remains, then we convert these to a selection dict, which is then
    # filtered to contain only Choices that exactly match the actual FP values and attributes.

    # Step 1: Eliminate Choices not matching the actual FP values.
    for uuid in vardict:
        fp = uuid_to_fp(board, uuid)
        fp_value = fp.GetValue()
        fp_fields = get_fp_fields(fp)

        if use_attr_excl_from_bom():      fp_excl_bom = fp.IsExcludedFromBOM()
        if use_attr_excl_from_posfiles(): fp_excl_pos = fp.IsExcludedFromPosFiles()
        if use_attr_dnp():                fp_dnp      = fp.IsDNP()

        aspect = vardict[uuid][key_aspect()]
        # Check each remaining Choice whether it can be eliminated.
        # For value and attributes
        eliminate_choices = []
        for choice in choices[aspect]:
            fp_choice_value = vardict[uuid][key_main()][choice][key_value()]
            fp_choice_unfit = opt_unfit() in vardict[uuid][key_main()][choice][key_options()]
            eliminate = False

            if fp_choice_value is not None:
                if fp_value != fp_choice_value: eliminate = True

            # TODO these should only be compared if their checkboxes are checked or the config requests it.

            if use_attr_excl_from_bom():
                if fp_excl_bom != fp_choice_unfit: eliminate = True

            if use_attr_excl_from_posfiles():
                if fp_excl_pos != fp_choice_unfit: eliminate = True

            if use_attr_dnp():
                if fp_dnp != fp_choice_unfit: eliminate = True

            for field in vardict[uuid][key_aux()]:
                field_choice_value = vardict[uuid][key_aux()][field][choice][key_value()]
                # Future note: If any options are added for aux rules, check them here
                if field_choice_value is not None:
                    if fp_fields[field] != field_choice_value: eliminate = True

            # defer elimination until after iteration
            if eliminate: eliminate_choices.append(choice)

        for choice in eliminate_choices: choices[aspect].remove(choice)

    # Step 2: Create a dict with candidate Choices.
    selection = {}
    for choice in choices:
        if len(choices[choice]) == 1: selection[choice] = choices[choice][0]
        else:                         selection[choice] = None

    # Step 3: Eliminate candidate Choices that do not exactly match the required conditions.
    #         (Basically, this is a dry-run of the apply function.)
    for uuid in vardict:
        fp = uuid_to_fp(board, uuid)
        fp_value = fp.GetValue()
        fp_fields = get_fp_fields(fp)
        aspect = vardict[uuid][key_aspect()]
        if use_attr_excl_from_bom():      fp_excl_bom = fp.IsExcludedFromBOM()
        if use_attr_excl_from_posfiles(): fp_excl_pos = fp.IsExcludedFromPosFiles()
        if use_attr_dnp():                fp_dnp      = fp.IsDNP()
        selected_choice = selection[aspect]
        if selected_choice is not None:
            new_value = vardict[uuid][key_main()][selected_choice][key_value()]
            new_unfit = opt_unfit() in vardict[uuid][key_main()][selected_choice][key_options()]
            mismatch = False
            if new_value is not None:
                if fp_value != new_value: mismatch = True
            if use_attr_excl_from_bom():
                if fp_excl_bom != new_unfit: mismatch = True
            if use_attr_excl_from_posfiles():
                if fp_excl_pos != new_unfit: mismatch = True
            if use_attr_dnp():
                if fp_dnp != new_unfit: mismatch = True
            for field in vardict[uuid][key_aux()]:
                new_field_value = vardict[uuid][key_aux()][field][selected_choice][key_value()]
                if new_field_value is not None:
                    if new_field_value != fp_fields[field]: mismatch = True
            if mismatch: selection[aspect] = None
    return selection

def apply_choices(board, vardict, selection, dry_run = False):
    changes = []
    for uuid in vardict:
        fp = uuid_to_fp(board, uuid)
        ref = fp.GetReferenceAsString()
        aspect = vardict[uuid][key_aspect()]
        old_fp_fields = get_fp_fields(fp)
        selected_choice = selection[aspect]
        if selected_choice is not None:
            choice_text = f'{quote_str(aspect)}={quote_str(selected_choice)}'
            new_value = vardict[uuid][key_main()][selected_choice][key_value()]
            if new_value is not None:
                old_value = fp.GetValue()
                if old_value != new_value:
                    changes.append([uuid, f"Change {ref} value from '{escape_str(old_value)}' to '{escape_str(new_value)}' ({choice_text})."])
                    if not dry_run: fp.SetValue(new_value)
            new_unfit = opt_unfit() in vardict[uuid][key_main()][selected_choice][key_options()]
            if use_attr_dnp():
                old_dnp = fp.IsDNP()
                if old_dnp != new_unfit:
                    changes.append([uuid, f"Change {ref} 'Do not populate' from '{bool_as_text(old_dnp)}' to '{bool_as_text(new_unfit)}' ({choice_text})."])
                    if not dry_run: fp.SetDNP(new_unfit)
            if use_attr_excl_from_bom():
                old_excl_from_bom = fp.IsExcludedFromBOM()
                if old_excl_from_bom != new_unfit:
                    changes.append([uuid, f"Change {ref} 'Exclude from bill of materials' from '{bool_as_text(old_excl_from_bom)}' to '{bool_as_text(new_unfit)}' ({choice_text})."])
                    if not dry_run: fp.SetExcludedFromBOM(new_unfit)
            if use_attr_excl_from_posfiles():
                old_excl_from_posfiles = fp.IsExcludedFromPosFiles()
                if old_excl_from_posfiles != new_unfit:
                    changes.append([uuid, f"Change {ref} 'Exclude from position files' from '{bool_as_text(old_excl_from_posfiles)}' to '{bool_as_text(new_unfit)}' ({choice_text})."])
                    if not dry_run: fp.SetExcludedFromPosFiles(new_unfit)
            for field in vardict[uuid][key_aux()]:
                new_field_value = vardict[uuid][key_aux()][field][selected_choice][key_value()]
                if new_field_value is not None:
                    if old_fp_fields[field] != new_field_value:
                        changes.append([uuid, f"Change {ref} field '{escape_str(field)}' from '{escape_str(old_fp_fields[field])}' to '{escape_str(new_field_value)}' ({choice_text})."])
                        if not dry_run: set_fp_field(fp, field, new_field_value)
    return changes

def add_choice(vardict, uuid, aspect, raw_choice_name, raw_choice_def, field=None, all_choices=None):
    # If field is passed, this handles aux rules, else main rules.
    is_aux = field is not None
    accepted_options = [] if is_aux else [opt_unfit()]
    try:
        raw_names = split_raw_str(raw_choice_name, ',', False)
    except Exception as e:
        return f"Choice names splitter error: {str(e)}."

    try:
        raw_args = split_raw_str(raw_choice_def, ' ', True)
    except Exception as e:
        return f"Choice arguments splitter error: {str(e)}."

    choices = []
    for choice_name in raw_names:
        cooked_name = cook_raw_string(choice_name)
        if cooked_name == '':
            return f"Variation choice name must not be empty."
        choices.append(cooked_name)

    values = []
    options = []
    for raw_arg in raw_args:
        arg = cook_raw_string(raw_arg)
        if raw_arg.startswith('-'): # not supposed to match if arg starts with \- or '-'
            option = arg[1:]
            if not option in accepted_options:
                return f"Unknown or invalid option '{option}'."
            options.append(option)
        else:
            values.append(arg)

    if len(values) > 1:
        return f"More than one value provided inside a choice definition." # TODO add info in which choice def (index value)

    if not is_aux: vardict[uuid][key_aspect()] = aspect

    for choice in choices:
        if not is_aux:
            if choice in vardict[uuid][key_main()]:
                return f"Multiple definitions."
            vardict[uuid][key_main()][choice] = {}
            vardict[uuid][key_main()][choice][key_value()] = values[0] if len(values) > 0 else None
            vardict[uuid][key_main()][choice][key_options()] = options
        else:
            if choice != key_default() and not choice in all_choices[aspect]:
                return f"Undeclared choice (aspect {quote_str(aspect)})."
            if choice in vardict[uuid][key_aux()][field]:
                return f"Multiple definitions."
            vardict[uuid][key_aux()][field][choice] = {}
            vardict[uuid][key_aux()][field][choice][key_value()] = values[0] if len(values) > 0 else None
            vardict[uuid][key_aux()][field][choice][key_options()] = options
    return None

def get_vardict(board):
    # TODO streamline all error messages to make clear where exactly the problem happened (main rule or aux rule, consistent wording!)
    vardict = {}
    errors = []
    fps = board.GetFootprints()
    fps.sort(key=lambda x: natural_sort_key(x.GetReference()))

    for fp in fps:
        uuid = fp_to_uuid(fp)
        ref = fp.GetReferenceAsString()
        my_fields = get_my_fp_fields(fp)
        rule = get_rule(my_fields)
        if rule is not None:
            if uuid in vardict:
                errors.append([uuid, f"{ref}: Multiple footprints with same UUID containing a rule definition field '{rule_field}'."])
                continue
            if len(rule) < 1:
                # field exists, but is empty. ignore it. a field containing only white-space is considered an error.
                continue
            vardict[uuid] = {}
            vardict[uuid][key_aspect()] = None
            vardict[uuid][key_main()] = {}
            vardict[uuid][key_aux()] = {}
            try:
                rule_sections = split_raw_str(rule, ' ', True)
            except Exception as e:
                errors.append([uuid, f"{ref}: Rule splitter error: {str(e)}."])
                continue
            # TODO clarify: shall we use uncooked aspect name? we have the whole field content only for the pure value.
            aspect = get_rule_aspect(my_fields)
            aspect_from_field = aspect is not None and len(aspect) > 0
            if not aspect_from_field:
                aspect = None
                if len(rule_sections) < 2:
                    errors.append([uuid, f"{ref}: Invalid number of elements in rule definition (expecting aspect name and at least one choice definition)."])
                    continue
            else:
                if len(rule_sections) < 1:
                    errors.append([uuid, f"{ref}: Invalid number of elements in rule definition (expecting at least one choice definition)."])
                    continue
            section_is_aspect_name = not aspect_from_field
            section_num = 0
            for section in rule_sections:
                section_num += 1
                try:
                    name, content = split_choice(section)
                except Exception as e:
                    errors.append([uuid, f"{ref}: Section splitter error: {str(e)}."])
                    continue
                if section_is_aspect_name:
                    # First rule section contains the Aspect name only (if not already defined by dedicated field)
                    # TODO clarify rules for Aspect name (forbidden characters: "*" ".")
                    section_is_aspect_name = False
                    cooked_name = cook_raw_string(name)
                    if cooked_name is None or cooked_name == '':
                        errors.append([uuid, f"{ref}: Variation aspect name must not be empty."])
                        continue
                    if content is not None:
                        errors.append([uuid, f"{ref}: Expecting variation aspect name in first rule section (or in dedicated field)."]) # TODO as a help, print out the dedicated field name
                        continue
                    aspect = cooked_name
                elif aspect is not None:
                    # Any following rule sections are Choice definitions.
                    if name is None or name == '':
                        errors.append([uuid, f"{ref}: Variation choice name list must not be empty."])
                        continue
                    if content is None:
                        if section_num == 1 and aspect_from_field:
                            errors.append([uuid, f"{ref}: Variation choice definition must have parenthesis (aspect name already defined in dedicated field)."])
                        else:
                            errors.append([uuid, f"{ref}: Variation choice definition must have parenthesis."])
                        continue
                    error_str = add_choice(vardict, uuid, aspect, name, content)
                    if error_str is not None:
                        # TODO cook and quote names in error message, refine wording
                        errors.append([uuid, f"{ref}: In definition of choice '{name}': {error_str}"])
                        continue
# TODO check ALL(!) continue statements if we can really continue, or we should break completely!!!!

    # Handle aux rules
    all_choices = get_choice_dict(vardict)
    for uuid in vardict:
        fp = uuid_to_fp(board, uuid)
        ref = fp.GetReferenceAsString()
        aspect = vardict[uuid][key_aspect()]
        # Parse aux assignments
        all_fields = get_fp_fields(fp)
        my_fields = get_my_fp_fields(fp)
        aux_fields = get_aux(my_fields)

        # TODO better save the assignment field names in orig. case (not lower()), at least to print correct error messages with orig name
        for field in aux_fields:
            # TODO case insens.?        if not field in [f.lower() for f in all_fields]:
            if not field in all_fields:
                errors.append([uuid, f"{ref}: Aux rule for non-existing field name '{field}'."]) # TODO escape field name?
                continue
            rule = aux_fields[field]
            if len(rule) < 1:
                # field exists, but is empty. ignore it.
                # a field containing only white-space is considered an error.
                continue
            try:
                rule_sections = split_raw_str(rule, ' ', True)
            except Exception as e:
                errors.append([uuid, f"{ref}: Aux rule splitter error for field '{field}': {str(e)}."]) # TODO escape field name?
                continue

            if field in vardict[uuid][key_aux()]:
                errors.append([uuid, f"{ref}: Multiple aux rule definitions for field '{field}'."])
                continue
            vardict[uuid][key_aux()][field] = {}
            if len(rule_sections) < 1:
                errors.append([uuid, f"{ref}: Invalid number of elements in aux rule definition for field '{field}' (expecting at least one choice definition)."])
                continue
            for section in rule_sections:
                try:
                    name, content = split_choice(section)
                except Exception as e:
                    errors.append([uuid, f"{ref}: Section splitter error in aux rule for field '{field}': {str(e)}."])
                    continue
                # In aux rules, all rule sections are Choice references.
                if name is None or name == '':
                    errors.append([uuid, f"{ref}: Variation choice name list must not be empty in aux rule for field '{field}'."])
                    continue
                if content is None:
                    errors.append([uuid, f"{ref}: Variation choice definition must have parenthesis in aux rule for field '{field}'."])
                    continue
                error_str = add_choice(vardict, uuid, aspect, name, content, field, all_choices)
                if error_str is not None:
                    # TODO cook and quote names in error message, refine wording
                    errors.append([uuid, f"{ref}: In aux rule for field '{field}', choice '{name}': {error_str}"])
                    continue

        # Flatten definition sub-dict, assign default values
        choices_with_value_defined = 0
        for choice in all_choices[aspect]:
            if choice in vardict[uuid][key_main()]: # TODO check that each Choice is contained exactly ONCE!
                if vardict[uuid][key_main()][choice][key_value()] is None:
                    # There is a specific Choice definition, but it does not contain a value.
                    # Take the value from the Default Choice (if it exists), keep the options
                    # as defined in the specific Choice definition.
                    if key_default() in vardict[uuid][key_main()]:
                        vardict[uuid][key_main()][choice][key_value()] = vardict[uuid][key_main()][key_default()][key_value()]
            else:
                # The specific Choice definition is missing. Copy value and options from Default
                # Choice definition (if it exists).
                vardict[uuid][key_main()][choice] = {}
                if key_default() in vardict[uuid][key_main()]:
                    value = vardict[uuid][key_main()][key_default()][key_value()]
                    options = vardict[uuid][key_main()][key_default()][key_options()]
                else:
                    value = None
                    options = []
                vardict[uuid][key_main()][choice][key_value()] = value
                vardict[uuid][key_main()][choice][key_options()] = options

            if vardict[uuid][key_main()][choice][key_value()] is not None:
                choices_with_value_defined += 1

        if not (choices_with_value_defined == 0 or choices_with_value_defined == len(all_choices[aspect])):
            errors.append([uuid, f"{ref}: Rule mixes choices with defined ({choices_with_value_defined}) and undefined ({len(all_choices[aspect]) - choices_with_value_defined}) values (either all or none must be defined)."])
            continue

        # Remove default choice entries from main sub-dict
        vardict[uuid][key_main()].pop(key_default(), None)

        # Flatten aux sub-dict, assign default values
        for field in vardict[uuid][key_aux()]:
            choices_with_value_defined = 0
            for choice in all_choices[aspect]:
                if choice in vardict[uuid][key_aux()][field]: # TODO check that each Choice is contained exactly ONCE!
                    if vardict[uuid][key_aux()][field][choice][key_value()] is None:
                        # There is a specific Choice definition, but it does not contain a value.
                        # Take the value from the Default Choice (if it exists), keep the options
                        # as defined in the specific Choice definition.
                        if key_default() in vardict[uuid][key_aux()][field]:
                            vardict[uuid][key_aux()][field][choice][key_value()] = vardict[uuid][key_aux()][field][key_default()][key_value()]
                else:
                    # The specific Choice definition is missing. Copy value and options from Default
                    # Choice definition (if it exists).
                    vardict[uuid][key_aux()][field][choice] = {}
                    if key_default() in vardict[uuid][key_aux()][field]:
                        value = vardict[uuid][key_aux()][field][key_default()][key_value()]
                        options = vardict[uuid][key_aux()][field][key_default()][key_options()]
                    else:
                        value = None
                        options = []
                    vardict[uuid][key_aux()][field][choice][key_value()] = value
                    vardict[uuid][key_aux()][field][choice][key_options()] = options

                if vardict[uuid][key_aux()][field][choice][key_value()] is not None:
                    choices_with_value_defined += 1

            if not (choices_with_value_defined == 0 or choices_with_value_defined == len(all_choices[aspect])):
                errors.append([uuid, f"{ref}: Aux rule for field '{field}' mixes choices with defined ({choices_with_value_defined}) and undefined ({len(all_choices[aspect]) - choices_with_value_defined}) values (either all or none must be defined)."])
                continue

            # Remove default choice entries from aux sub-dict
            vardict[uuid][key_aux()][field].pop(key_default(), None)
    return vardict, errors

def get_choice_dict(vardict):
    choices = {}
    for uuid in vardict:
        aspect = vardict[uuid][key_aspect()]
        if not aspect in choices: choices[aspect] = []
        for choice in vardict[uuid][key_main()]:
            # In case the input dict still contains temporary data (such as default data), ignore it.
            if choice != key_default() and not choice in choices[aspect]: choices[aspect].append(choice)
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
        if end_expected: raise ValueError('String extends beyond closing parenthesis')
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
            else:  raise ValueError('Unmatched closing parenthesis')
        else:
            item.append(c)
    if parens > 0: raise ValueError('Unmatched opening parenthesis')
    if quoted:     raise ValueError('Unmatched quote character in string')
    if escaped:    raise ValueError('Unterminated escape sequence at end of string')
    if len(item) > 0: outside = ''.join(item)
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
            else: raise ValueError('Unmatched closing parenthesis')
            item.append(c)
        elif c == sep and not quoted and parens == 0:
            if not multisep or len(item) > 0:
                result.append(''.join(item))
                item = []
        else:
            item.append(c)
    if parens > 0: raise ValueError('Unmatched opening parenthesis')
    if quoted:     raise ValueError('Unmatched quote character in string')
    if escaped:    raise ValueError('Unterminated escape sequence at end of string')
    if not multisep or len(item) > 0: result.append(''.join(item))
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
    if quoted:  raise ValueError('Unmatched quote character in string')
    if escaped: raise ValueError('Unterminated escape sequence at end of string')
    return ''.join(result)
