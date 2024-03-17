import pcbnew

# TODO more testing!

# TODO KiCad 7 API is currently not working. implement low-level stuff.

# TODO KiCad 8 has different reporting style, it seems. use this?
    # Remove R29 'Do not place' fabrication attribute.
    # Remove R29 'exclude from BOM' fabrication attribute.
    # Add R22 'exclude from BOM' fabrication attribute.
    # Add R22 'Do not place' fabrication attribute.
    # Update R2 fields.

# TODO for concatenated/nested error messages, period rule:
#      * exceptions do not include final period
#      * error messages include a period
#      * messages that append the returned error message do not contain the period

# TODO in field parser, accept only target fields, which are no KiVar fields themselves (avoid recursion!)

# TODO case-sensitivity concept! where and when do we lower-case names?
#      keep casing intact at least for reporting field names!

# TODO filter locked field names (reference, value, footprint (???)) for set AND get!!

# TODO finalize substrings for base and aux rule field names

# TODO clean-up implementation (more object-orientation, where useful)

# TODO clarify rules for Aspect name (forbidden characters: "*" ".")

def version():
    return '0.2.0-dev20'

def pcbnew_version():
    v = pcbnew.GetMajorMinorPatchVersion().split('.')
    return int(v[0]) * 100 + int(v[1])

def fp_to_uuid(fp):
    return fp.m_Uuid.AsString()

def uuid_to_fp(board, uuid):
    return board.GetItem(pcbnew.KIID(uuid)).Cast()

def get_fp_fields(fp):
    if pcbnew_version() < 799: fields = fp.GetProperties()
    else:                      fields = fp.GetFieldsText()
    return fields

def set_fp_field(fp, field, value):
    # TODO check behavior of KiCad 7 regarding built-in "fields" (is value mirrored/shadowed in field "value"?)
    if not field.lower() in ['value', 'reference', 'footprint']:
        if pcbnew_version() < 799: fp.SetProperty(field, value)
        else:                      fp.SetField(field, value)

def build_fpdict(board):
    fpdict = {}
    for fp in board.GetFootprints():
        uuid = fp_to_uuid(fp)
        # TODO check if UUID exists in dict!
        # TODO api version 7 might need dedicated getter/setter for value/datasheet etc...
        fpdict[uuid] = {}
        fpdict[uuid][key_fp_ref()] = fp.GetReferenceAsString()
        fpdict[uuid][key_fp_fields()] = get_fp_fields(fp)
        # TODO clean up, we currently store the value twice! (at least for api version 8, not sure about 7!)
        # the format is the same as for choice branches
        fpdict[uuid][key_value()] = fp.GetValue()
        fpdict[uuid][key_props()] = {}
        fpdict[uuid][key_props()][code_prop_bom()] = not fp.IsExcludedFromBOM()      if use_attr_excl_from_bom() else None
        fpdict[uuid][key_props()][code_prop_pos()] = not fp.IsExcludedFromPosFiles() if use_attr_excl_from_posfiles() else None
        fpdict[uuid][key_props()][code_prop_fit()] = not fp.IsDNP()                  if use_attr_dnp() else None
    return fpdict

def store_fpdict(board, fpdict):
    for uuid in fpdict:
        fp = uuid_to_fp(board, uuid)
        old_fp_value = fp.GetValue()
        new_fp_value = fpdict[uuid][key_value()]
        if old_fp_value != new_fp_value:
            fp.SetValue(new_fp_value)
        for prop_code in fpdict[uuid][key_props()]:
            new_prop_value = fpdict[uuid][key_props()][prop_code]
            if new_prop_value is not None:
                old_prop_value = None
                if   prop_code == code_prop_bom():
                    if use_attr_excl_from_bom(): old_prop_value = not fp.IsExcludedFromBOM()
                elif prop_code == code_prop_pos():
                    if use_attr_excl_from_posfiles(): old_prop_value = not fp.IsExcludedFromPosFiles()
                elif prop_code == code_prop_fit():
                    if use_attr_dnp(): old_prop_value = not fp.IsDNP()
                if old_prop_value is not None:
                    if old_prop_value != new_prop_value:
                        if   prop_code == code_prop_bom(): fp.SetExcludedFromBOM(not new_prop_value)
                        elif prop_code == code_prop_pos(): fp.SetExcludedFromPosFiles(not new_prop_value)
                        elif prop_code == code_prop_fit(): fp.SetDNP(not new_prop_value)
        # TODO api version 7 might need dedicated getter/setter for value/datasheet etc...
        old_fp_field_values = get_fp_fields(fp)
        for field in fpdict[uuid][key_fp_fields()]:
            old_fp_field_value = old_fp_field_values[field]
            new_fp_field_value = fpdict[uuid][key_fp_fields()][field]
            if old_fp_field_value != new_fp_field_value:
                set_fp_field(fp, field, new_fp_field_value)
    return fpdict

# TODO still required if we adopt KiCad 8 reporting style?
def bool_as_text(value):
    return 'true' if value == True else 'false'

def use_attr_dnp():
    return pcbnew_version() >= 799

def use_attr_excl_from_bom():
    return True

def use_attr_excl_from_posfiles():
    return True

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

# TODO use a cleaner way for keys
def key_aspect():    return 'a'
def key_base():      return 'b'
def key_aux():       return 'x'
def key_default():   return '*'
def key_value():     return 'v'
def key_props():     return 'p'
def opt_unfit():     return '!'
def key_fp_ref():    return 'R'
def key_fp_fields(): return 'F'

def code_prop_fit(): return 'f'
def code_prop_bom(): return 'b'
def code_prop_pos(): return 'p'

def base_prop_codes(): return code_prop_fit()+code_prop_bom()+code_prop_pos()

def supported_prop_codes(): return base_prop_codes()+'!'

def prop_state(props, prop):
    return props[prop] if prop in props else None

def prop_attrib_name(prop_code):
    name = '(unknown)'
    if   prop_code == code_prop_bom(): name = 'Exclude from bill of materials'
    elif prop_code == code_prop_pos(): name = 'Exclude from position files'
    elif prop_code == code_prop_fit(): name = 'Do not populate'
    return name

def prop_abbrev(prop_code):
    name = '(unknown)'
    if   prop_code == code_prop_bom(): name = 'BoM'
    elif prop_code == code_prop_pos(): name = 'Pos'
    elif prop_code == code_prop_fit(): name = 'Fit'
    return name

def mismatches_fp_choice(fpdict_branch, vardict_choice_branch):
    # TODO in returned mismatches, add mismatching fp and choice states
    mismatches = []
    choice_value = vardict_choice_branch[key_value()]
    fp_value = fpdict_branch[key_value()]
    if choice_value is not None and fp_value != choice_value:
        mismatches.append('value')
    for prop_code in base_prop_codes():
        choice_prop = prop_state(vardict_choice_branch[key_props()], prop_code)
        fp_prop = prop_state(fpdict_branch[key_props()], prop_code)
        if choice_prop is not None and fp_prop is not None and choice_prop != fp_prop:
            mismatches.append(f"prop '{prop_code}'")
    return mismatches

def mismatches_fp_choice_aux(fp_fields, vardict_aux_branch, choice):
    # TODO in returned mismatches, add mismatching fp and choice states
    mismatches = []
    for field in vardict_aux_branch:
        choice_field_value = vardict_aux_branch[field][choice][key_value()]
        if choice_field_value is not None and choice_field_value != fp_fields[field]:
            mismatches.append(f"field '{field}' for choice '{choice}'")
    return mismatches

def detect_current_choices(fpdict, vardict):
    # We start with the usual Choice dict filled with all possible Choices per Aspect and then
    # eliminate all Choices whose values do not exactly match the actual FP values, fields or attributes.
    # If exactly one Choice per Aspect remains, then we add this choice to the selection dict.
    choices = get_choice_dict(vardict)
    # Eliminate Choices not matching the actual FP values.
    for uuid in vardict:
        fp_ref = fpdict[uuid][key_fp_ref()]
        aspect = vardict[uuid][key_aspect()]
        eliminate_choices = []
        for choice in choices[aspect]:
            eliminate = False
            mismatches = mismatches_fp_choice(fpdict[uuid], vardict[uuid][key_base()][choice])
            if mismatches: eliminate = True
            mismatches = mismatches_fp_choice_aux(fpdict[uuid][key_fp_fields()], vardict[uuid][key_aux()], choice)
            if mismatches: eliminate = True
            # defer elimination until after iteration
            if eliminate: eliminate_choices.append(choice)
        for choice in eliminate_choices: choices[aspect].remove(choice)
    # Create a dict with candidate Choices. Report Choices only if they are unambiguous.
    selection = {}
    for aspect in choices:
        if len(choices[aspect]) == 1: selection[aspect] = choices[aspect][0]
        else:                         selection[aspect] = None
    return selection

def apply_selection(fpdict, vardict, selection, dry_run = False):
    changes = []
    for uuid in vardict:
        ref = fpdict[uuid][key_fp_ref()]
        aspect = vardict[uuid][key_aspect()]
        selected_choice = selection[aspect]
        if selected_choice is not None:
            choice_text = f'{quote_str(aspect)}={quote_str(selected_choice)}'
            new_value = vardict[uuid][key_base()][selected_choice][key_value()]
            if new_value is not None:
                old_value = fpdict[uuid][key_value()]
                if old_value != new_value:
                    changes.append([uuid, f"Change {ref} value from '{escape_str(old_value)}' to '{escape_str(new_value)}' ({choice_text})."])
                    if not dry_run: fpdict[uuid][key_value()] = new_value
            for prop_code in base_prop_codes():
                new_prop = vardict[uuid][key_base()][selected_choice][key_props()][prop_code]
                if new_prop is not None:
                    old_prop = fpdict[uuid][key_props()][prop_code]
                    if old_prop is not None and old_prop != new_prop:
                        changes.append([uuid, f"Change {ref} '{prop_attrib_name(prop_code)}' from '{bool_as_text(not old_prop)}' to '{bool_as_text(not new_prop)}' ({choice_text})."])
                        if not dry_run: fpdict[uuid][key_props()][prop_code] = new_prop
            for field in vardict[uuid][key_aux()]:
                new_field_value = vardict[uuid][key_aux()][field][selected_choice][key_value()]
                if new_field_value is not None:
                    old_field_value = fpdict[uuid][key_fp_fields()][field]
                    if old_field_value != new_field_value:
                        changes.append([uuid, f"Change {ref} field '{escape_str(field)}' from '{escape_str(old_field_value)}' to '{escape_str(new_field_value)}' ({choice_text})."])
                        if not dry_run: fpdict[uuid][key_fp_fields()][field] = new_field_value
    return changes

def parse_prop_str(prop_str):
    prop_set = {}
    state = None
    expect_prop = False
    for prop_code in prop_str:
        if prop_code in '+-':
            if expect_prop: raise ValueError(f"Invalid syntax: Expecting property code after state modifier.")
            expect_prop = True
            state = prop_code == '+'
        else:
            expect_prop = False
            if state is None: raise ValueError(f"Undefined property state for code '{prop_code}'.")
            if not prop_code in supported_prop_codes(): raise ValueError(f"Unsupported property code '{prop_code}'.")
            # TODO add a '?' symbol, which can be defined by the user
            if prop_code == '!':
                for c in base_prop_codes(): prop_set[c] = state
            else:
                prop_set[prop_code] = state
    if expect_prop: raise ValueError(f"Invalid syntax: Property set ends with state modifier.")
    return prop_set

def add_choice(vardict, uuid, raw_choice_name, raw_choice_def, field=None, all_aspect_choices=None):
    """ Adds a choice set (base or aux rule definition) to the vardict. """
    # TODO add unique error codes (for aux rules, add an offset), for unit testing (do not compare error strings).
    # If field is passed, this handles aux rules, else base rules.
    is_aux = field is not None
    try:
        raw_names = split_raw_str(raw_choice_name, ',', False)
    except Exception as e:
        return [f"Choice names splitter error for choice set '{raw_choice_name}': {str(e)}."] # TODO cook name?
    try:
        raw_args = split_raw_str(raw_choice_def, ' ', True)
    except Exception as e:
        return [f"Choice arguments splitter error for choice def '{raw_choice_def}': {str(e)}."]
    choices = []
    for choice_name in raw_names:
        cooked_name = cook_raw_string(choice_name)
        if cooked_name == '':
            return ["Empty choice name."]
        choices.append(cooked_name)
    errors = []
    value = None
    prop_strs = []
    for raw_arg in raw_args:
        arg = cook_raw_string(raw_arg)
        if raw_arg[0] in '-+': # not supposed to match if arg starts with \-, \+, '+' or '-'
            if is_aux:
                errors.append(f"Properties not allowed for aux rules.")
                continue
            prop_strs.append(arg)
        else:
            if value is not None:
                errors.append(f"Illegal additional value argument ('{arg}') for choice set '{raw_choice_name}'.")
                continue
            value = arg
    for choice in choices:
        if is_aux:
            if choice != key_default() and not choice in all_aspect_choices:
                errors.append(f"Undeclared choice '{choice}'.") # TODO print aspect in caller.### (in aspect {quote_str(aspect)}).")
                continue
            if not field in vardict[uuid][key_aux()]: vardict[uuid][key_aux()][field] = {}
            vardict_branch = vardict[uuid][key_aux()][field]
        else:
            vardict_branch = vardict[uuid][key_base()]
        if not choice in vardict_branch:
            vardict_branch[choice] = {}
            vardict_branch[choice][key_value()] = None
            vardict_branch[choice][key_props()] = {}
        if value is not None:
            if vardict_branch[choice][key_value()] is not None:
                errors.append(f"Illegal additional value '{value}' assignment for choice '{choice}'.")
                continue
            vardict_branch[choice][key_value()] = value
        for prop_str in prop_strs:
            try:
                prop_set = parse_prop_str(prop_str)
            except Exception as error:
                errors.append(f"Property set parser error: {str(error)}.")
                continue
            for prop_code in prop_set:
                if not prop_code in vardict_branch[choice][key_props()]:
                    vardict_branch[choice][key_props()][prop_code] = None
                if vardict_branch[choice][key_props()][prop_code] is not None:
                    errors.append(f"Multiple {prop_abbrev(prop_code)} property value assignments for choice '{choice}'.")
                    continue
                vardict_branch[choice][key_props()][prop_code] = prop_set[prop_code]
    return errors

def finalize_vardict_branch(vardict_choice_branch, all_aspect_choices, is_aux = False):
    """ Finalizes (flattens) a branch of the vardict (either base rules or aux rules). """
    errors = []
    # Flatten values
    # TODO instead of counting, append (quoted) name of choice to two lists,
    #      then print their content (joined with comma) in the error messages!
    choices_with_value_defined = 0
    for choice in all_aspect_choices:
        if not choice in vardict_choice_branch:
            vardict_choice_branch[choice] = {}
            vardict_choice_branch[choice][key_value()] = None
            vardict_choice_branch[choice][key_props()] = {}

        if key_default() in vardict_choice_branch:
            if vardict_choice_branch[choice][key_value()] is None:
                vardict_choice_branch[choice][key_value()] = vardict_choice_branch[key_default()][key_value()]

        if vardict_choice_branch[choice][key_value()] is not None:
            choices_with_value_defined += 1
    if not (choices_with_value_defined == 0 or choices_with_value_defined == len(all_aspect_choices)):
        errors.append(f"Rule mixes choices with defined ({choices_with_value_defined}) and undefined ({len(all_aspect_choices) - choices_with_value_defined}) values (either all or none must be defined).")
    if not is_aux:
        # Flatten properties
        for prop_code in base_prop_codes():
            default_prop_value = None
            if key_default() in vardict_choice_branch and prop_code in vardict_choice_branch[key_default()][key_props()] and vardict_choice_branch[key_default()][key_props()][prop_code] is not None:
                # defined default prop value available, use it
                default_prop_value = vardict_choice_branch[key_default()][key_props()][prop_code]
            else:
                # try to determine an implicit default value
                choices_with_true = 0
                choices_with_false = 0
                for choice in all_aspect_choices:
                    if prop_code in vardict_choice_branch[choice][key_props()] and vardict_choice_branch[choice][key_props()][prop_code] is not None:
                        if vardict_choice_branch[choice][key_props()][prop_code]: choices_with_true  += 1
                        else:                                                     choices_with_false += 1
                # if only set x-or clear is used in (specific) choices, the implicit default is the opposite.
                if   choices_with_false and not choices_with_true: default_prop_value = True
                elif not choices_with_false and choices_with_true: default_prop_value = False
            choices_with_prop_defined = 0
            for choice in all_aspect_choices:
                if not prop_code in vardict_choice_branch[choice][key_props()] or vardict_choice_branch[choice][key_props()][prop_code] is None:
                    vardict_choice_branch[choice][key_props()][prop_code] = default_prop_value
                if vardict_choice_branch[choice][key_props()][prop_code] is not None:
                    choices_with_prop_defined += 1

            if not (choices_with_prop_defined == 0 or choices_with_prop_defined == len(all_aspect_choices)):
                errors.append(f"Rule mixes choices with defined ({choices_with_prop_defined}) and undefined ({len(all_aspect_choices) - choices_with_prop_defined}) {prop_abbrev(prop_code)} property ('{prop_code}') state (either all or none must be defined).")
    # Remove default choice entries from branch
    vardict_choice_branch.pop(key_default(), None)
    return errors

def parse_rule_str(rule_str):
    errors = []
    aspects = []
    choice_sets = []
    if rule_str is not None:
        try:
            rule_sections = split_raw_str(rule_str, ' ', True)
        except Exception as error:
            return [f'Rule splitter: {str(error)}'], None, None
        for section in rule_sections:
            try:
                name_list, content = split_parens(section)
            except Exception as error:
                errors.append(f'Section splitter: {str(error)}')
                continue
            if content is None: # None means: no parens
                # this is an aspect name. cook and store.
                try:
                    cooked_name = cook_raw_string(name_list)
                except Exception as error:
                    errors.append(f'Aspect name parser: {str(error)}')
                    continue
                if cooked_name is None or cooked_name == '':
                    errors.append('Aspect name must not be empty')
                    continue
                aspects.append(cooked_name)
            else:
                # this is a choice definition. leave name and content raw and store.
                if name_list is None or name_list == '':
                    errors.append('Choice name list must not be empty')
                    continue
                choice_sets.append([name_list, content])
    return errors, aspects, choice_sets

def parse_rule_fields(fpdict_uuid_branch):
    errors = []
    aspect = None
    base_rule_string = None
    base_choice_sets = []
    aux_rule_strings = []
    aux_choice_sets = []
    for fp_field in fpdict_uuid_branch[key_fp_fields()]:
        value = fpdict_uuid_branch[key_fp_fields()][fp_field]
        # field names that are not properly formatted are ignored and do not cause
        # an error message. we don't want to misinterpret user's fields.
        try: parts = split_raw_str(fp_field, '.', False)
        except: continue
        # TODO use dedicated getters for strings/lists
        if len(parts) == 3 and parts[0] == 'KiVar' and parts[1] == 'Rule' and parts[2] == 'Aspect': # TODO remove "Rule"
            aspect = value
        elif len(parts) == 2 and parts[0] == 'KiVar' and parts[1] == 'Rule': # TODO remove "Rule"
            base_rule_string = value
        elif len(parts) > 1 and parts[-1] == 'KiVar':
            target_field = '.'.join(parts[0:-1])
            aux_rule_strings.append([target_field, value])
        else:
            try: prefix, name_list = split_parens(parts[-1])
            except: continue
            if prefix == 'KiVar':
                try: parts_in_parens = split_raw_str(name_list, ' ', True)
                except: continue
                if len(parts_in_parens) > 1:
                    errors.append(f"Illegal space character in choice name list '{name_list}'")
                    continue
                if len(parts) == 1:
                    base_choice_sets.append([name_list, value])
                else:
                    target_field = '.'.join(parts[0:-1])
                    aux_choice_sets.append([target_field, name_list, value])
    return errors, aspect, base_rule_string, base_choice_sets, aux_rule_strings, aux_choice_sets

def build_vardict(fpdict):
    vardict = {}
    errors = []
    auxdict = {}
    # Handle base rule
    for uuid in fpdict:
        ref = fpdict[uuid][key_fp_ref()]
        parse_errors, aspect, base_rule_string, base_choice_sets, aux_rule_strings, aux_choice_sets = parse_rule_fields(fpdict[uuid])
        if parse_errors:
            for parse_error in parse_errors: errors.append([uuid, f"{ref}: When parsing rule fields: {parse_error}."])
            continue
        parse_errors, aspects, choice_sets = parse_rule_str(base_rule_string)
        if parse_errors:
            for parse_error in parse_errors: errors.append([uuid, f"{ref}: When parsing base rule string: {parse_error}."])
            continue
        choice_sets.extend(base_choice_sets)
        if not choice_sets: continue
        # TODO decide: shall we really use uncooked aspect name? we have the whole field content only for the pure value.
        if len(aspects) > 1:
            errors.append([uuid, f"{ref}: Multiple aspect name definitions in base rule."])
            continue
        elif len(aspects) == 1:
            # about to use the aspect name from the base rule ...
            if aspect is not None and aspect != '':
                # ... but there is already an aspect set via the aspect field
                errors.append([uuid, f"{ref}: Conflicting aspect name definition styles (base rule string vs. aspect field)."])
                continue
            aspect = aspects[0]
        if aspect is None or aspect == '':
            errors.append([uuid, f"{ref}: Missing aspect name definition."])
            continue
        if uuid in vardict:
            errors.append([uuid, f"{ref}: Multiple footprints with same UUID containing a base rule definition."])
            continue
        vardict[uuid] = {}
        vardict[uuid][key_aspect()] = aspect
        vardict[uuid][key_base()] = {}
        vardict[uuid][key_aux()] = {}
        auxdict[uuid] = [aux_rule_strings, aux_choice_sets] # save for aux loop
        for choice_name, choice_content in choice_sets:
            add_errors = add_choice(vardict, uuid, choice_name, choice_content)
            if add_errors:
                for error in add_errors: errors.append([uuid, f"{ref}: When adding base rule aspect '{aspect}' choice list '{choice_name}': {error}."])
                break
    # Handle aux rules
    all_choices = get_choice_dict(vardict)
    for uuid in vardict:
        ref = fpdict[uuid][key_fp_ref()]
        aspect = vardict[uuid][key_aspect()]
        aux_rule_strings, aux_choice_sets = auxdict[uuid]
        if aux_rule_strings and aspect is None:
            errors.append([uuid, f"{ref}: Aux rule strings found, but missing base rule definition."]) # TODO terminology
            continue
        valid = False
        for field, rule_str in aux_rule_strings:
            if not field in fpdict[uuid][key_fp_fields()]:
                # TODO move this check to the fields parser?
                errors.append([uuid, f"{ref}: Aux rule string for non-existing field name '{field}'."]) # TODO escape field name?
                continue
            if rule_str is None or rule_str == '': continue
            parse_errors, aspects, choice_sets = parse_rule_str(rule_str)
            if parse_errors:
                for parse_error in parse_errors: errors.append([uuid, f"{ref}: When parsing aux rule for field '{field}': {parse_error}."])
                continue
            if aspects:
                errors.append([uuid, f"{ref}: Aux rule for field '{field}' contains an aspect name (only allowed for base rule)."])
                continue
            if field in vardict[uuid][key_aux()]:
                errors.append([uuid, f"{ref}: Multiple aux rule definitions for field '{field}'."])
                continue
            for choice_name, choice_content in choice_sets:
                add_errors = add_choice(vardict, uuid, choice_name, choice_content, field, all_choices[aspect])
                if add_errors:
                    for error in add_errors: errors.append([uuid, f"{ref}: When adding aux rule aspect '{aspect}' choice list '{choice_name}' for field '{field}': {error}."])
                    break
        else:
            valid = True
        if not valid: continue
        if aux_choice_sets and aspect is None:
            errors.append([uuid, f"{ref}: Aux rule choice fields found, but missing base rule definition."]) # TODO terminology
            continue
        valid = False
        for field, choice_name, choice_content in aux_choice_sets:
            add_errors = add_choice(vardict, uuid, choice_name, choice_content, field, all_choices[aspect])
            if add_errors:
                # TODO different error text than above!
                for error in add_errors: errors.append([uuid, f"{ref}: When adding aux rule aspect '{aspect}' choice list '{choice_name}' for field '{field}': {error}."])
                break
        else:
            valid = True
        if not valid: continue
        fin_errors = finalize_vardict_branch(vardict[uuid][key_base()], all_choices[aspect], is_aux=False)
        if fin_errors:
            # TODO cook and quote names in error message, refine wording
            for e in fin_errors: errors.append([uuid, f"{ref}: In base rule: {e}"])
            continue
        for field in vardict[uuid][key_aux()]:
            fin_errors = finalize_vardict_branch(vardict[uuid][key_aux()][field], all_choices[aspect], is_aux=True)
            if fin_errors:
                # TODO cook and quote names in error message, refine wording
                for e in fin_errors: errors.append([uuid, f"{ref}: In aux rule for field '{field}': {e}"])
                continue
    if errors: vardict = {} # make sure an incomplete vardict cannot be used by the caller
    return vardict, errors

def get_choice_dict(vardict):
    choices = {}
    for uuid in vardict:
        aspect = vardict[uuid][key_aspect()]
        if not aspect in choices: choices[aspect] = []
        for choice in vardict[uuid][key_base()]:
            # In case the input dict still contains temporary data (such as default data), ignore it.
            if choice != key_default() and not choice in choices[aspect]: choices[aspect].append(choice)
    return choices

def split_parens(str):
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
    if item: outside = ''.join(item)
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
            if not multisep or item:
                result.append(''.join(item))
                item = []
        else:
            item.append(c)
    if parens > 0: raise ValueError('Unmatched opening parenthesis')
    if quoted:     raise ValueError('Unmatched quote character in string')
    if escaped:    raise ValueError('Unterminated escape sequence at end of string')
    if not multisep or item: result.append(''.join(item))
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
