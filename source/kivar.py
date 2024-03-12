import pcbnew

# TODO more testing!

# TODO review all continue statements! decide whether it makes sense to continue and where. and which post-actions should be skipped on break.

# TODO KiCad 7 API is currently not working. implement low-level stuff.

# TODO KiCad 8 has different reporting style, it seems. use this?
    # Remove R29 'Do not place' fabrication attribute.
    # Remove R29 'exclude from BOM' fabrication attribute.
    # Add R22 'exclude from BOM' fabrication attribute.
    # Add R22 'Do not place' fabrication attribute.
    # Update R2 fields.

# TODO case-sensitivity concept! where and when do we lower-case names?
#      keep casing intact at least for reporting field names!

# TODO filter locked field names (reference, value, footprint (???)) for set AND get!!

# TODO finalize format how to specify main and aux rules

# TODO clean-up implementation (more object-orientation)

def version():
    return '0.2.0-dev15'

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

# TODO unify
def get_rule(fields):
    key = 'KiVar.Rule' # lower-case! TODO
    # if key in fields:
    #     return fields[key]
    # else:
    #     print(f'Debug: no main rule found.')
    #     return None
    return fields[key] if key in fields else None

# TODO unify
def get_rule_aspect(fields):
    key = 'KiVar.Rule.Aspect' # lower-case! TODO
    return fields[key] if key in fields else None

# TODO unify
def get_aux(fields):
    result = {}
    prefix = 'KiVar.Aux.' # lower-case! TODO
    for f in fields:
        if f.startswith(prefix):
            # TODO check for invalid characters in referenced field name (period, etc.)
            result[f[len(prefix):]] = fields[f]
    return result

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
def key_main():      return 'd'
def key_aux():       return 'x'
def key_default():   return '*'
def key_value():     return 'v'
def key_props():     return 'p'
def opt_unfit():     return '!'
def key_fp_ref():    return 'R'
def key_fp_fields(): return 'F'

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
    choices = get_choice_dict(vardict)

    # How it works:
    # We start with the usual Choice dict filled with all possible Choices per Aspect.
    # Then we eliminate all Choices whose values do not match the actual FP values (or attributes).
    # If exactly one Choice per Aspect remains, then we convert these to a selection dict.
# TODO remove step 3? old text:
#    # , which is then
#    # filtered to contain only Choices that exactly match the actual FP values and attributes.

    # Step 1: Eliminate Choices not matching the actual FP values.
    for uuid in vardict:
        fp_ref = fpdict[uuid][key_fp_ref()]
        aspect = vardict[uuid][key_aspect()]
        eliminate_choices = []
        for choice in choices[aspect]:
            eliminate = False
            mismatches = mismatches_fp_choice(fpdict[uuid], vardict[uuid][key_main()][choice])
            if len(mismatches) > 0: eliminate = True
            mismatches = mismatches_fp_choice_aux(fpdict[uuid][key_fp_fields()], vardict[uuid][key_aux()], choice)
            if len(mismatches) > 0: eliminate = True
            # defer elimination until after iteration
            if eliminate: eliminate_choices.append(choice)
        for choice in eliminate_choices: choices[aspect].remove(choice)

    # Step 2: Create a dict with candidate Choices. Report Choices only if they are unambiguous.
    selection = {}
    for aspect in choices:
        if len(choices[aspect]) == 1: selection[aspect] = choices[aspect][0]
        else:                         selection[aspect] = None

    # Step 3: Eliminate candidate Choices that do not exactly match the required conditions.
    # TODO check again ... why exactly is this (still??) required? we do the same as above, don't we???
    # for uuid in vardict:
    #     aspect = vardict[uuid][key_aspect()]
    #     choice = selection[aspect]
    #     if choice is not None:
    #         eliminate = False
    #         mismatches = mismatches_fp_choice(fpdict[uuid], vardict[uuid][key_main()][choice])
    #         if len(mismatches) > 0: eliminate = True
    #         mismatches = mismatches_fp_choice_aux(fpdict[uuid][key_fp_fields()], vardict[uuid][key_aux()], choice)
    #         if len(mismatches) > 0: eliminate = True
    #         if eliminate: selection[aspect] = None
    return selection

def apply_selection(fpdict, vardict, selection, dry_run = False):
    changes = []
    for uuid in vardict:
        ref = fpdict[uuid][key_fp_ref()]
        aspect = vardict[uuid][key_aspect()]
        selected_choice = selection[aspect]
        if selected_choice is not None:
            choice_text = f'{quote_str(aspect)}={quote_str(selected_choice)}'
            new_value = vardict[uuid][key_main()][selected_choice][key_value()]
            if new_value is not None:
                old_value = fpdict[uuid][key_value()]
                if old_value != new_value:
                    changes.append([uuid, f"Change {ref} value from '{escape_str(old_value)}' to '{escape_str(new_value)}' ({choice_text})."])
                    if not dry_run: fpdict[uuid][key_value()] = new_value
            for prop_code in base_prop_codes():
                new_prop = vardict[uuid][key_main()][selected_choice][key_props()][prop_code]
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

def code_prop_fit(): return 'f'
def code_prop_bom(): return 'b'
def code_prop_pos(): return 'p'

def base_prop_codes(): return code_prop_fit()+code_prop_bom()+code_prop_pos()
def supported_prop_codes(): return base_prop_codes()+'!'

def handle_prop(props, prop_code, state):
    if not prop_code in supported_prop_codes(): return f"Unsupported property code '{prop_code}'."
    # TODO add a '?' symbol, which can be defined by the user
    if prop_code == '!':
        for p in base_prop_codes(): props[p] = state
    else:
        props[prop_code] = state

# TODO more syntax checking.
#      forbidden: "-+-+" (polarity change without prop inbetween)
#                 "+b-" (polarity change at end of string)
#                 etc ...
def handle_prop_str(props, prop_str):
    state = None
    for c in prop_str:
        if   c == '-': state = False
        elif c == '+': state = True
        else:
            if state is None: return f"Undefined property state for code '{c}'."
            error = handle_prop(props, c, state)
            if error is not None: return error

def add_choice(vardict, uuid, aspect, raw_choice_name, raw_choice_def, field=None, all_aspect_choices=None):
    """ Adds a choice set (main or aux rule definition) to the vardict. """
    # TODO add unique error codes (for aux rules, add an offset), for unit testing (do not compare error strings).
    # TODO allow multiple errors and continue/break here, too? we do this in many other places to enable the user to find as many problems in a single run.
    # If field is passed, this handles aux rules, else main rules.
    is_aux = field is not None
    try:
        raw_names = split_raw_str(raw_choice_name, ',', False)
    except Exception as e:
        return f"Choice names splitter error for choice set '{raw_choice_name}': {str(e)}." # TODO cook name?

    try:
        raw_args = split_raw_str(raw_choice_def, ' ', True)
    except Exception as e:
        return f"Choice arguments splitter error for choice def '{raw_choice_def}': {str(e)}."

    choices = []
    for choice_name in raw_names:
        cooked_name = cook_raw_string(choice_name)
        if cooked_name == '':
            return "Empty choice name."
        choices.append(cooked_name)

    value = None
    prop_strs = []
    for raw_arg in raw_args:
        arg = cook_raw_string(raw_arg)
        if raw_arg[0] in '-+': # not supposed to match if arg starts with \-, \+, '+' or '-'
            if is_aux:
                return f"Properties not allowed for aux rules."
            prop_strs.append(arg)
        else:
            if value is not None:
                return f"Multiple value arguments provided for choice set '{raw_choice_name}'."
            value = arg

    if not is_aux: vardict[uuid][key_aspect()] = aspect

    for choice in choices:
        if is_aux:
            if choice != key_default() and not choice in all_aspect_choices:
                return f"Undeclared choice '{choice}' (in aspect {quote_str(aspect)})."
            vardict_branch = vardict[uuid][key_aux()][field]
        else:
            vardict_branch = vardict[uuid][key_main()]
        if not choice in vardict_branch:
            vardict_branch[choice] = {}
            vardict_branch[choice][key_value()] = None
            vardict_branch[choice][key_props()] = {}
        if value is not None:
            if vardict_branch[choice][key_value()] is not None:
                return f"Multiple value assignments for choice '{choice}'."
            vardict_branch[choice][key_value()] = value
        for prop_str in prop_strs:
            error = handle_prop_str(vardict_branch[choice][key_props()], prop_str)
            if error is not None: return error
    return None

def finalize_vardict_branch(vardict_choice_branch, all_aspect_choices, is_aux = False):
    """ Finalizes (flattens) a branch of the vardict (either main rules or aux rules). """
    errors = []
    # Flatten values
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
                if   choices_with_false > 0 and choices_with_true == 0: default_prop_value = True
                elif choices_with_false == 0 and choices_with_true > 0: default_prop_value = False
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

def build_vardict(fpdict):
    # TODO streamline all error messages to make clear where exactly the problem happened (main rule or aux rule, consistent wording!)
    vardict = {}
    errors = []

    # TODO unify rule handling for main and aux rules.
    #      aspect name is either already known (via .Aspect=...) or not. if not known and main rule and not as 1st arg -> error.
    for uuid in fpdict:
        ref = fpdict[uuid][key_fp_ref()]
        rule = get_rule(fpdict[uuid][key_fp_fields()])
        if rule is None or len(rule) < 1: continue
        if uuid in vardict:
            errors.append([uuid, f"{ref}: Multiple footprints with same UUID containing a rule definition field '{rule_field}'."])
            continue
        vardict[uuid] = {}
        vardict[uuid][key_aspect()] = None
        vardict[uuid][key_main()] = {}
        vardict[uuid][key_aux()] = {}
        try:
            rule_sections = split_raw_str(rule, ' ', True)
        except Exception as error:
            errors.append([uuid, f"{ref}: Rule splitter error: {str(error)}."])
            continue
        # TODO clarify: shall we use uncooked aspect name? we have the whole field content only for the pure value.
        aspect = get_rule_aspect(fpdict[uuid][key_fp_fields()])
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
            except Exception as error:
                errors.append([uuid, f"{ref}: Section splitter error: {str(error)}."])
                break
            if section_is_aspect_name:
                # First rule section contains the Aspect name only (if not already defined by dedicated field)
                # TODO clarify rules for Aspect name (forbidden characters: "*" ".")
                section_is_aspect_name = False
                cooked_name = cook_raw_string(name)
                if cooked_name is None or cooked_name == '':
                    errors.append([uuid, f"{ref}: Aspect name must not be empty."])
                    break
                if content is not None:
                    errors.append([uuid, f"{ref}: Expecting aspect name in first rule section (or in dedicated field)."]) # TODO as a help, print out the dedicated field name
                    break
                aspect = cooked_name
            elif aspect is not None:
                # Any following rule sections are Choice definitions.
                if name is None or name == '':
                    errors.append([uuid, f"{ref}: Choice name list must not be empty."])
                    break
                if content is None:
                    if section_num == 1 and aspect_from_field:
                        errors.append([uuid, f"{ref}: Choice definition must have parenthesis (aspect name already defined in dedicated field)."])
                    else:
                        errors.append([uuid, f"{ref}: Choice definition must have parenthesis."])
                    break
                error_str = add_choice(vardict, uuid, aspect, name, content)
                if error_str is not None:
                    # TODO cook and quote names in error message, refine wording
                    errors.append([uuid, f"{ref}: In main rule: {error_str}"])
                    break

# TODO fix break/else/continue!!

    # Handle aux rules
    all_choices = get_choice_dict(vardict)
    for uuid in vardict:
        ref = fpdict[uuid][key_fp_ref()]
        aspect = vardict[uuid][key_aspect()]
        # Parse aux assignments
        aux_fields = get_aux(fpdict[uuid][key_fp_fields()])

        # TODO better save the assignment field names in orig. case (not lower()), at least to print correct error messages with orig name

        if len(aux_fields) > 0 and aspect is None:
            errors.append([uuid, f"{ref}: Aux rules missing main rule definition."])
            continue

        valid = False
        for field in aux_fields:
            # TODO case insens.?        if not field in [f.lower() for f in all_fields]:
            if not field in fpdict[uuid][key_fp_fields()]:
                errors.append([uuid, f"{ref}: Aux rule for non-existing field name '{field}'."]) # TODO escape field name?
                continue
            rule = aux_fields[field]
            if len(rule) < 1:
                # field exists, but is empty. ignore it.
                # a field containing only white-space is considered an error.
                continue
            try:
                rule_sections = split_raw_str(rule, ' ', True)
            except Exception as error:
                errors.append([uuid, f"{ref}: Aux rule splitter error for field '{field}': {str(error)}."]) # TODO escape field name?
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
                except Exception as error:
                    errors.append([uuid, f"{ref}: Section splitter error in aux rule for field '{field}': {str(error)}."])
                    break
                # In aux rules, all rule sections are Choice references.
                if name is None or name == '':
                    errors.append([uuid, f"{ref}: Variation choice name list must not be empty in aux rule for field '{field}'."])
                    break
                if content is None:
                    errors.append([uuid, f"{ref}: Variation choice definition must have parenthesis in aux rule for field '{field}'."])
                    break
                error_str = add_choice(vardict, uuid, aspect, name, content, field, all_choices[aspect])
                if error_str is not None:
                    # TODO cook and quote names in error message, refine wording
                    errors.append([uuid, f"{ref}: In aux rule for field '{field}': {error_str}"])
                    break
        else:
            valid = True
        if not valid: continue

        fin_errors = finalize_vardict_branch(vardict[uuid][key_main()], all_choices[aspect], is_aux=False)
        if len(fin_errors) > 0:
            for e in fin_errors:
                # TODO cook and quote names in error message, refine wording
                errors.append([uuid, f"{ref}: In main rule: {e}"])
            continue

        for field in vardict[uuid][key_aux()]:
            fin_errors = finalize_vardict_branch(vardict[uuid][key_aux()][field], all_choices[aspect], is_aux=True)
            if len(fin_errors) > 0:
                for e in fin_errors:
                    # TODO cook and quote names in error message, refine wording
                    errors.append([uuid, f"{ref}: In aux rule for field '{field}': {e}"])
                continue
    if len(errors) > 0: vardict = {} # make sure an incomplete vardict cannot be used by the caller
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
