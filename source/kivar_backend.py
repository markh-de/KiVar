import pcbnew
from copy import deepcopy

# Note about field case-sensitivity:
# As long as KiCad can easily be tricked* into having multiple fields whose names only differ in casing, we
# will not allow case-insensitive field parsing/assignment.
# * Even though the symbol editor does not allow having "Var" and "VAR" at the same time, you can rename a field
#   to "VAR" and will still get the field name template "Var" presented, which you can fill with a value and KiCad
#   will even save that field to your file.

# TODO pre-sort errors and changes before returning them, ready to be used by caller. then remove sorting and
#      requirements (e.g. Key class import) in callers.

# TODO clarify rules for Aspect name (forbidden characters: "*" ".")

# TODO in aux field parser, accept only target fields which are no KiVar fields themselves (avoid recursion!)

# TODO wrap the backend with a class.

# TODO more testing!

# TODO KiCad 8 has different change reporting style, it seems. use this?
    # Remove R29 'Do not place' fabrication attribute.
    # Remove R29 'exclude from BOM' fabrication attribute.
    # Add R22 'exclude from BOM' fabrication attribute.
    # Add R22 'Do not place' fabrication attribute.
    # Update R2 fields.
#     ^^^ this "update fields" message is too generic.

def version():
    return '0.2.1'

def pcbnew_compatibility_error():
    ver = pcbnew.GetMajorMinorPatchVersion()
    schema = ver.split('.')
    num = int(schema[0]) * 100 + int(schema[1])
    return None if num >= 799 else f'This version of KiVar requires KiCad pcbnew version 7.99 or later.\nYou are using pcbnew version {ver}.'

def fp_to_uuid(fp):
    return fp.m_Uuid.AsString()

def uuid_to_fp(board, uuid):
    return board.GetItem(pcbnew.KIID(uuid)).Cast()

def field_accepted(field_name):
    return not field_name.lower() in ['value', 'reference', 'footprint']

def set_fp_field(fp, field, value):
    if field_accepted(field): fp.SetField(field, value)

def legacy_expressions_found(fpdict):
    found = 0
    for uuid in fpdict:
        for field in fpdict[uuid][Key.FIELDS]:
            if field == 'KiVar.Rule' and fpdict[uuid][Key.FIELDS][field]: found += 1
    return found

def build_fpdict(board):
    fpdict = {}
    for fp in board.GetFootprints():
        uuid = fp_to_uuid(fp)
        # if UUID is already known, skip any footprint with same UUID.
        # TODO return error if same UUIDs are found. silently ignoring entries is bad.
        if not uuid in fpdict:
            fpdict[uuid] = {}
            fpdict[uuid][Key.REF] = fp.GetReferenceAsString()
            fields_text = fp.GetFieldsText()
            fpdict[uuid][Key.FIELDS] = {}
            for field in fields_text:
                if field_accepted(field): fpdict[uuid][Key.FIELDS][field] = fields_text[field]
            fpdict[uuid][Key.VALUE] = fp.GetValue()
            fpdict[uuid][Key.PROPS] = {}
            fpdict[uuid][Key.PROPS][PropCode.BOM] = not fp.IsExcludedFromBOM()
            fpdict[uuid][Key.PROPS][PropCode.POS] = not fp.IsExcludedFromPosFiles()
            fpdict[uuid][Key.PROPS][PropCode.FIT] = not fp.IsDNP()
    return fpdict

def store_fpdict(board, fpdict):
    for uuid in fpdict:
        fp = uuid_to_fp(board, uuid)
        old_fp_value = fp.GetValue()
        new_fp_value = fpdict[uuid][Key.VALUE]
        if old_fp_value != new_fp_value:
            fp.SetValue(new_fp_value)
        for prop_code in fpdict[uuid][Key.PROPS]:
            new_prop_value = fpdict[uuid][Key.PROPS][prop_code]
            if new_prop_value is not None:
                old_prop_value = None
                if   prop_code == PropCode.BOM: old_prop_value = not fp.IsExcludedFromBOM()
                elif prop_code == PropCode.POS: old_prop_value = not fp.IsExcludedFromPosFiles()
                elif prop_code == PropCode.FIT: old_prop_value = not fp.IsDNP()
                if old_prop_value is not None:
                    if old_prop_value != new_prop_value:
                        if   prop_code == PropCode.BOM: fp.SetExcludedFromBOM(not new_prop_value)
                        elif prop_code == PropCode.POS: fp.SetExcludedFromPosFiles(not new_prop_value)
                        elif prop_code == PropCode.FIT: fp.SetDNP(not new_prop_value)
        old_fp_field_values = fp.GetFieldsText()
        for field in fpdict[uuid][Key.FIELDS]:
            old_fp_field_value = old_fp_field_values[field]
            new_fp_field_value = fpdict[uuid][Key.FIELDS][field]
            if old_fp_field_value != new_fp_field_value:
                set_fp_field(fp, field, new_fp_field_value)
    return fpdict

# TODO still required if we adopt KiCad 8 reporting style?
def bool_as_text(value):
    return 'true' if value == True else 'false'

def natural_sort_key(string):
    key = []
    part = ''
    for c in string:
        if c.isdigit(): part += c
        else:
            if part:
                key.append((0, int(part), ''))
                part = ''
            key.append((1, 0, c.lower()))
    if part: key.append((0, int(part), ''))
    return key

def escape_str(string):
    result = ''
    for c in string:
        if c == '\\' or c == "'" or c == '"': result += '\\'
        result += c
    return result

def quote_str(string):
    # we prefer single-quotes for output
    if string == '': result = "''"
    else:
        if any(c in string for c in ', -\\()="\''):
            q = '"' if string.count("'") > string.count('"') else "'"
            result = q
            for c in string:
                if c == '\\' or c == q: result += '\\'
                result += c
            result += q
        else: result = string
    return result

# TODO use a cleaner way for keys
class Key:
    DEFAULT = '*' # relevant for user interface, rest of keys only used internally
    ASPECT  = 'a'
    BASE    = 'b'
    AUX     = 'x'
    VALUE   = 'v'
    PROPS   = 'p'
    REF     = 'R'
    FIELDS  = 'F'

class PropCode: # all of these must be uppercase
    FIT = 'F'
    BOM = 'B'
    POS = 'P'

class FieldID: # case-sensitive
    BASE   = 'Var'
    ASPECT = 'Aspect'

class PropGroup:
    ALL = '!'

def base_prop_codes(): return PropCode.FIT + PropCode.BOM + PropCode.POS

def supported_prop_codes(): return base_prop_codes() + PropGroup.ALL

def prop_state(props, prop):
    return props[prop] if prop in props else None

def prop_attrib_name(prop_code):
    if   prop_code == PropCode.BOM: name = 'Exclude from bill of materials'
    elif prop_code == PropCode.POS: name = 'Exclude from position files'
    elif prop_code == PropCode.FIT: name = 'Do not populate'
    else:                           name = '(unknown)'
    return name

def prop_abbrev(prop_code):
    if   prop_code == PropCode.BOM: name = 'BoM'
    elif prop_code == PropCode.POS: name = 'Pos'
    elif prop_code == PropCode.FIT: name = 'Fit'
    else:                           name = '(unknown)'
    return name

def mismatches_fp_choice(fpdict_branch, vardict_choice_branch):
    # TODO in returned mismatches, add mismatching fp and choice states
    mismatches = []
    choice_value = vardict_choice_branch[Key.VALUE]
    fp_value = fpdict_branch[Key.VALUE]
    if choice_value is not None and fp_value != choice_value:
        mismatches.append('value')
    for prop_code in base_prop_codes():
        choice_prop = prop_state(vardict_choice_branch[Key.PROPS], prop_code)
        fp_prop = prop_state(fpdict_branch[Key.PROPS], prop_code)
        if choice_prop is not None and fp_prop is not None and choice_prop != fp_prop:
            mismatches.append(f"prop '{prop_code}'")
    return mismatches

def mismatches_fp_choice_aux(fp_fields, vardict_aux_branch, choice):
    # TODO in returned mismatches, add mismatching fp and choice states
    mismatches = []
    for field in vardict_aux_branch:
        choice_field_value = vardict_aux_branch[field][choice][Key.VALUE]
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
        fp_ref = fpdict[uuid][Key.REF]
        aspect = vardict[uuid][Key.ASPECT]
        eliminate_choices = []
        for choice in choices[aspect]:
            eliminate = False
            mismatches = mismatches_fp_choice(fpdict[uuid], vardict[uuid][Key.BASE][choice])
            if mismatches: eliminate = True
            mismatches = mismatches_fp_choice_aux(fpdict[uuid][Key.FIELDS], vardict[uuid][Key.AUX], choice)
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
        ref = fpdict[uuid][Key.REF]
        aspect = vardict[uuid][Key.ASPECT]
        if not aspect in selection: continue
        selected_choice = selection[aspect]
        if selected_choice is None: continue
        choice_text = f'{quote_str(aspect)}={quote_str(selected_choice)}'
        new_value = vardict[uuid][Key.BASE][selected_choice][Key.VALUE]
        if new_value is not None:
            old_value = fpdict[uuid][Key.VALUE]
            if old_value != new_value:
                changes.append([uuid, ref, f"Change {ref} value from '{escape_str(old_value)}' to '{escape_str(new_value)}' ({choice_text})."])
                if not dry_run: fpdict[uuid][Key.VALUE] = new_value
        for prop_code in base_prop_codes():
            new_prop = vardict[uuid][Key.BASE][selected_choice][Key.PROPS][prop_code]
            if new_prop is not None:
                old_prop = fpdict[uuid][Key.PROPS][prop_code]
                if old_prop is not None and old_prop != new_prop:
                    changes.append([uuid, ref, f"Change {ref} '{prop_attrib_name(prop_code)}' from '{bool_as_text(not old_prop)}' to '{bool_as_text(not new_prop)}' ({choice_text})."])
                    if not dry_run: fpdict[uuid][Key.PROPS][prop_code] = new_prop
        for field in vardict[uuid][Key.AUX]:
            new_field_value = vardict[uuid][Key.AUX][field][selected_choice][Key.VALUE]
            if new_field_value is not None:
                old_field_value = fpdict[uuid][Key.FIELDS][field]
                if old_field_value != new_field_value:
                    changes.append([uuid, ref, f"Change {ref} field '{escape_str(field)}' from '{escape_str(old_field_value)}' to '{escape_str(new_field_value)}' ({choice_text})."])
                    if not dry_run: fpdict[uuid][Key.FIELDS][field] = new_field_value
    return changes

def parse_prop_str(prop_str, old_prop_set={}):
    prop_set = old_prop_set.copy() # TODO as a dict, this is pass-by-reference, so we could simply overwrite the old prop_set and return only errors
    state = None
    expect_prop = False
    for prop_code in prop_str.upper():
        if prop_code in '+-':
            if expect_prop: raise ValueError(f"Property modifier must be followed by property identifier")
            expect_prop = True
            state = prop_code == '+'
        else:
            expect_prop = False
            if state is None: raise ValueError(f"Undefined property modifier for identifier '{prop_code}'") # should never happen
            if not prop_code in supported_prop_codes(): raise ValueError(f"Unsupported property identifier '{prop_code}'")
            # TODO add a '?' symbol, which can be defined by the user
            if prop_code == PropGroup.ALL:
                for c in base_prop_codes(): prop_set[c] = state
            else:
                prop_set[prop_code] = state
    if expect_prop: raise ValueError(f"Property specifier must not end with a modifier, but with an identifier")
    return prop_set

def add_choice(vardict, uuid, raw_choice_name, raw_choice_def, field=None, all_aspect_choices=None):
    """ Adds a choice set (base or aux rule definition) to the vardict. """
    # TODO add unique error codes (for aux rules, add an offset), for unit testing (do not compare error strings).
    # If field is passed, this handles aux rules, else base rules.
    is_aux = field is not None
    try:
        raw_names = split_raw_str(raw_choice_name, ',', False)
    except Exception as e:
        return [f"Choice identifiers splitter error for identifier list '{raw_choice_name}': {str(e)}"] # TODO cook name?
    try:
        raw_args = split_raw_str(raw_choice_def, ' ', True)
    except Exception as e:
        return [f"Choice arguments splitter error for argument list '{raw_choice_def}': {str(e)}"]
    choices = []
    for choice_name in raw_names:
        cooked_name = cook_raw_string(choice_name)
        if cooked_name == '':
            return ["Empty choice identifier"]
        choices.append(cooked_name)
    errors = []
    values = []
    prop_set = {}
    for raw_arg in raw_args:
        arg = cook_raw_string(raw_arg)
        if raw_arg[0] in '-+': # not supposed to match if arg starts with \-, \+, '+' or '-'
            if is_aux:
                errors.append(f"No property specifier allowed in aux expression")
                continue
            try:
                prop_set = parse_prop_str(arg, prop_set)
            except Exception as error:
                errors.append(f"Property specifier parser error: {str(error)}")
                continue
        else:
            values.append(arg)
    for choice in choices:
        if is_aux:
            if choice != Key.DEFAULT and not choice in all_aspect_choices:
                errors.append(f"Undeclared choice identifier '{choice}'") # TODO print aspect in caller.### (in aspect {quote_str(aspect)})")
                continue
            if not field in vardict[uuid][Key.AUX]: vardict[uuid][Key.AUX][field] = {}
            vardict_branch = vardict[uuid][Key.AUX][field]
        else:
            vardict_branch = vardict[uuid][Key.BASE]
        if not choice in vardict_branch:
            vardict_branch[choice] = {}
            vardict_branch[choice][Key.VALUE] = None
            vardict_branch[choice][Key.PROPS] = {}
        if values:
            value = ' '.join(values)
            if vardict_branch[choice][Key.VALUE] is None:
                vardict_branch[choice][Key.VALUE] = value
            else:
                errors.append(f"Illegal additional content '{value}' assignment for choice '{choice}'")
        for prop_code in prop_set:
            if not prop_code in vardict_branch[choice][Key.PROPS]:
                vardict_branch[choice][Key.PROPS][prop_code] = None
            if vardict_branch[choice][Key.PROPS][prop_code] is None:
                vardict_branch[choice][Key.PROPS][prop_code] = prop_set[prop_code]
            else:
                errors.append(f"Illegal additional '{prop_abbrev(prop_code)}' property assignment for choice '{choice}'")
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
            vardict_choice_branch[choice][Key.VALUE] = None
            vardict_choice_branch[choice][Key.PROPS] = {}
        if Key.DEFAULT in vardict_choice_branch:
            if vardict_choice_branch[choice][Key.VALUE] is None:
                vardict_choice_branch[choice][Key.VALUE] = vardict_choice_branch[Key.DEFAULT][Key.VALUE]
        if vardict_choice_branch[choice][Key.VALUE] is not None:
            choices_with_value_defined += 1
    if not (choices_with_value_defined == 0 or choices_with_value_defined == len(all_aspect_choices)):
        errors.append(f"Mixed choices with defined ({choices_with_value_defined}x) and undefined ({len(all_aspect_choices) - choices_with_value_defined}x) content (either all or none must be defined)")
    if not is_aux:
        # Flatten properties
        for prop_code in base_prop_codes():
            default_prop_value = None
            if Key.DEFAULT in vardict_choice_branch and prop_code in vardict_choice_branch[Key.DEFAULT][Key.PROPS] and vardict_choice_branch[Key.DEFAULT][Key.PROPS][prop_code] is not None:
                # defined default prop value available, use it
                default_prop_value = vardict_choice_branch[Key.DEFAULT][Key.PROPS][prop_code]
            else:
                # try to determine an implicit default value
                choices_with_true = 0
                choices_with_false = 0
                for choice in all_aspect_choices:
                    if prop_code in vardict_choice_branch[choice][Key.PROPS] and vardict_choice_branch[choice][Key.PROPS][prop_code] is not None:
                        if vardict_choice_branch[choice][Key.PROPS][prop_code]: choices_with_true  += 1
                        else:                                                     choices_with_false += 1
                # if only set x-or clear is used in (specific) choices, the implicit default is the opposite.
                if   choices_with_false and not choices_with_true: default_prop_value = True
                elif not choices_with_false and choices_with_true: default_prop_value = False
            choices_with_prop_defined = 0
            for choice in all_aspect_choices:
                if not prop_code in vardict_choice_branch[choice][Key.PROPS] or vardict_choice_branch[choice][Key.PROPS][prop_code] is None:
                    vardict_choice_branch[choice][Key.PROPS][prop_code] = default_prop_value
                if vardict_choice_branch[choice][Key.PROPS][prop_code] is not None:
                    choices_with_prop_defined += 1
            if not (choices_with_prop_defined == 0 or choices_with_prop_defined == len(all_aspect_choices)):
                errors.append(f"Mixed choices with defined ({choices_with_prop_defined}x) and undefined ({len(all_aspect_choices) - choices_with_prop_defined}x) {prop_abbrev(prop_code)} property ('{prop_code}') state (either all or none must be defined)")
    # Remove default choice entries from branch
    vardict_choice_branch.pop(Key.DEFAULT, None)
    return errors

def parse_rule_str(rule_str):
    errors = []
    aspects = []
    choice_sets = []
    if rule_str is not None:
        try:
            rule_sections = split_raw_str(rule_str, ' ', True)
        except Exception as error:
            return [f'Combined format splitter: {str(error)}'], None, None
        for section in rule_sections:
            try:
                name_list, content = split_parens(section)
            except Exception as error:
                errors.append(f'Choice expression splitter: {str(error)}')
                continue
            if content is None: # None means: no parens
                # this is an aspect name. cook and store.
                try:
                    cooked_name = cook_raw_string(name_list)
                except Exception as error:
                    errors.append(f'Aspect identifier parser: {str(error)}')
                    continue
                if cooked_name is None or cooked_name == '':
                    errors.append('Aspect identifier must not be empty')
                    continue
                aspects.append(cooked_name)
            else:
                # this is a choice definition. leave name and content raw and store.
                if name_list is None or name_list == '':
                    errors.append('Choice identifier list must not be empty')
                    continue
                choice_sets.append([name_list, content])
    return errors, aspects, choice_sets

def field_name_check(field_name, available_fields):
    error = None
    if not field_accepted(field_name):
        error = f"Target field '{field_name}' is forbidden" # TODO escape field name
    elif not field_name in available_fields:
        error = f"Target field '{field_name}' does not exist" # TODO escape field name
    return error

def parse_rule_fields(fpdict_uuid_branch):
    errors = []
    aspect = None
    base_rule_string = None
    base_choice_sets = []
    aux_rule_strings = []
    aux_choice_sets = []
    for fp_field in fpdict_uuid_branch[Key.FIELDS]:
        value = fpdict_uuid_branch[Key.FIELDS][fp_field]
        # field names that are not properly formatted are ignored and do not cause
        # an error message. we don't want to misinterpret user's fields.
        try: parts = split_raw_str(fp_field, '.', False)
        except: continue
        if len(parts) == 2 and parts[0] == FieldID.BASE and parts[1] == FieldID.ASPECT:
            aspect = value
        elif len(parts) == 1 and parts[0] == FieldID.BASE:
            base_rule_string = value
        elif len(parts) > 1 and parts[-1] == FieldID.BASE:
            target_field = '.'.join(parts[0:-1])
            field_name_error = field_name_check(target_field, fpdict_uuid_branch[Key.FIELDS])
            if field_name_error is not None:
                errors.append(f"Combined aux expression: {field_name_error}")
                continue
            else:
                aux_rule_strings.append([target_field, value])
        else:
            try: prefix, name_list = split_parens(parts[-1])
            except: continue
            if prefix == FieldID.BASE:
                try: parts_in_parens = split_raw_str(name_list, ' ', True)
                except: continue
                if len(parts_in_parens) > 1:
                    errors.append(f"Choice identifier list '{name_list}' contains illegal space character")
                    continue
                if len(parts) == 1:
                    base_choice_sets.append([name_list, value])
                else:
                    target_field = '.'.join(parts[0:-1])
                    field_name_error = field_name_check(target_field, fpdict_uuid_branch[Key.FIELDS])
                    if field_name_error is not None:
                        errors.append(f"Simple aux expression: {field_name_error}")
                        continue
                    else:
                        aux_choice_sets.append([target_field, name_list, value])
    return errors, aspect, base_rule_string, base_choice_sets, aux_rule_strings, aux_choice_sets

def build_vardict(fpdict):
    vardict = {}
    errors = []
    auxdict = {}
    # Handle base rule
    for uuid in fpdict:
        ref = fpdict[uuid][Key.REF]
        parse_errors, aspect, base_rule_string, base_choice_sets, aux_rule_strings, aux_choice_sets = parse_rule_fields(fpdict[uuid])
        if parse_errors:
            for parse_error in parse_errors: errors.append([uuid, ref, f"{ref}: Field parser: {parse_error}."])
            continue
        parse_errors, aspects, choice_sets = parse_rule_str(base_rule_string)
        if parse_errors:
            for parse_error in parse_errors: errors.append([uuid, ref, f"{ref}: Base scope expression parser: {parse_error}."])
            continue
        choice_sets.extend(base_choice_sets)
        # TODO decide: shall we really use uncooked aspect name? we have the whole field content only for the pure value.
        if len(aspects) > 1:
            errors.append([uuid, ref, f"{ref}: Multiple aspect identifiers specified."])
            continue
        elif len(aspects) == 1:
            # about to use the aspect name from the base rule ...
            if aspect is not None and aspect != '':
                # ... but there is already an aspect set via the aspect field
                errors.append([uuid, ref, f"{ref}: Conflicting aspect identifier specification styles (combined base expression vs. aspect field)."])
                continue
            aspect = aspects[0]
        if aspect is None or aspect == '':
            if choice_sets:
                errors.append([uuid, ref, f"{ref}: Missing aspect identifier for existing choice expressions."])
            continue
        if uuid in vardict:
            errors.append([uuid, ref, f"{ref}: Multiple footprints with same UUID containing base expressions."])
            continue
        vardict[uuid] = {}
        vardict[uuid][Key.ASPECT] = aspect
        vardict[uuid][Key.BASE] = {}
        vardict[uuid][Key.AUX] = {}
        auxdict[uuid] = [aux_rule_strings, aux_choice_sets] # save for aux loop
        for choice_name, choice_content in choice_sets:
            add_errors = add_choice(vardict, uuid, choice_name, choice_content)
            if add_errors:
                for error in add_errors: errors.append([uuid, ref, f"{ref}: When adding aspect '{aspect}' choice list '{choice_name}' in base expression: {error}."])
                break
    # Handle aux rules
    all_choices = get_choice_dict(vardict)
    for uuid in auxdict:
        aux_rule_strings, aux_choice_sets = auxdict[uuid]
        ref = fpdict[uuid][Key.REF]
        aspect = vardict[uuid][Key.ASPECT]
        if aux_rule_strings and aspect is None:
            errors.append([uuid, ref, f"{ref}: Combined aux expression(s) found, but missing base expression(s)."])
            continue
        valid = False
        for field, rule_str in aux_rule_strings:
            if rule_str is None or rule_str == '': continue
            parse_errors, aspects, choice_sets = parse_rule_str(rule_str)
            if parse_errors:
                for parse_error in parse_errors: errors.append([uuid, ref, f"{ref}: Combined aux expression parser for target field '{field}': {parse_error}."])
                continue
            if aspects:
                errors.append([uuid, ref, f"{ref}: Combined aux expression for target field '{field}' contains what looks like an aspect identifier (only allowed in combined base expressions)."])
                continue
            if field in vardict[uuid][Key.AUX]:
                errors.append([uuid, ref, f"{ref}: Multiple aux expressions for target field '{field}'."]) # TODO wording
                continue
            for choice_name, choice_content in choice_sets:
                add_errors = add_choice(vardict, uuid, choice_name, choice_content, field, all_choices[aspect])
                if add_errors:
                    for error in add_errors: errors.append([uuid, ref, f"{ref}: Combined aux expression for aspect '{aspect}' choice list '{choice_name}' with target field '{field}': {error}."])
                    break
        else:
            valid = True
        if not valid: continue
        if aux_choice_sets and aspect is None:
            errors.append([uuid, ref, f"{ref}: Simple aux expression(s) found, but missing base expression(s)."])
            continue
        valid = False
        for field, choice_name, choice_content in aux_choice_sets:
            add_errors = add_choice(vardict, uuid, choice_name, choice_content, field, all_choices[aspect])
            if add_errors:
                for error in add_errors: errors.append([uuid, ref, f"{ref}: Simple aux expression for aspect '{aspect}' choice list '{choice_name}' with target field '{field}': {error}."])
                break
        else:
            valid = True
        if not valid: continue
        fin_errors = finalize_vardict_branch(vardict[uuid][Key.BASE], all_choices[aspect], is_aux=False)
        if fin_errors:
            # TODO cook and quote names in error message, refine wording
            for e in fin_errors: errors.append([uuid, ref, f"{ref}: In base expression: {e}."])
            continue
        for field in vardict[uuid][Key.AUX]:
            fin_errors = finalize_vardict_branch(vardict[uuid][Key.AUX][field], all_choices[aspect], is_aux=True)
            if fin_errors:
                # TODO cook and quote names in error message, refine wording
                for e in fin_errors: errors.append([uuid, ref, f"{ref}: In aux expression for target field '{field}': {e}."])
                continue
    if not errors:
        # Check for ambiguous choices (only if data is valid so far)
        for aspect in sorted(all_choices, key=natural_sort_key):
            choices = sorted(all_choices[aspect], key=natural_sort_key)
            for choice_a in choices:
                fpdict_a = deepcopy(fpdict)
                apply_selection(fpdict_a, vardict, {aspect: choice_a})
                ambiguous = []
                for choice_b in choices:
                    if choice_a == choice_b:
                        if ambiguous: break
                        else: continue
                    fpdict_b = deepcopy(fpdict)
                    apply_selection(fpdict_b, vardict, {aspect: choice_b})
                    if fpdict_a == fpdict_b: ambiguous.append(f"'{escape_str(choice_b)}'")
                if ambiguous:
                    errors.append([None, '0', f"Illegal ambiguity: Aspect '{escape_str(aspect)}' choice '{escape_str(choice_a)}' is identical with choice(s) {', '.join(ambiguous)}."])
                    break
    if errors: vardict = {} # make sure an incomplete vardict cannot be used by the caller
    return vardict, errors

def get_choice_dict(vardict):
    choices = {}
    for uuid in vardict:
        aspect = vardict[uuid][Key.ASPECT]
        if not aspect in choices: choices[aspect] = []
        for choice in vardict[uuid][Key.BASE]:
            # In case the input dict still contains temporary data (such as default data), ignore it.
            if choice != Key.DEFAULT and not choice in choices[aspect]: choices[aspect].append(choice)
    return choices

def split_parens(string):
    item = []
    outside = None
    inside = None
    escaped = False
    quoted_s = False
    quoted_d = False
    parens = 0
    end_expected = False
    for c in string:
        if end_expected: raise ValueError('String extends beyond closing parenthesis')
        elif escaped:
            escaped = False
            item.append(c)
        elif c == '\\':
            escaped = True
            item.append(c)
        elif c == "'" and not quoted_d:
            quoted_s = not quoted_s
            item.append(c)
        elif c == '"' and not quoted_s:
            quoted_d = not quoted_d
            item.append(c)
        elif c == '(' and not (quoted_s or quoted_d):
            parens += 1
            if parens == 1:
                outside = ''.join(item)
                inside = '' # inside: no parens -> None, empty parens -> ''
                item = []
            else:
                item.append(c)
        elif c == ')' and not (quoted_s or quoted_d):
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
    if parens:   raise ValueError('Unmatched opening parenthesis')
    if escaped:  raise ValueError('Unterminated escape sequence (\\) at end of string')
    if quoted_s: raise ValueError("Unmatched single-quote (') character in string")
    if quoted_d: raise ValueError('Unmatched double-quote (") character in string')
    if item: outside = ''.join(item)
    return outside, inside

def split_raw_str(str, sep, multisep):
    result = []
    item = []
    escaped = False
    quoted_s = False
    quoted_d = False
    parens = 0
    for c in str:
        if escaped:
            escaped = False
            item.append(c)
        elif c == '\\':
            escaped = True
            item.append(c)
        elif c == "'" and not quoted_d:
            quoted_s = not quoted_s
            item.append(c)
        elif c == '"' and not quoted_s:
            quoted_d = not quoted_d
            item.append(c)
        elif c == '(' and not (quoted_s or quoted_d):
            parens += 1
            item.append(c)
        elif c == ')' and not (quoted_s or quoted_d):
            if parens > 0:
                parens -= 1
            else: raise ValueError('Unmatched closing parenthesis')
            item.append(c)
        elif c == sep and not (quoted_s or quoted_d) and parens == 0:
            if not multisep or item:
                result.append(''.join(item))
                item = []
        else:
            item.append(c)
    if parens:   raise ValueError('Unmatched opening parenthesis')
    if escaped:  raise ValueError('Unterminated escape sequence (\\) at end of string')
    if quoted_s: raise ValueError("Unmatched single-quote (') character in string")
    if quoted_d: raise ValueError('Unmatched double-quote (") character in string')
    if not multisep or item: result.append(''.join(item))
    return result

def cook_raw_string(string):
    result = []
    escaped  = False
    quoted_s = False
    quoted_d = False
    for c in string:
        if escaped:
            result.append(c)
            escaped = False
        elif c == '\\':
            escaped = True
        elif c == "'" and not quoted_d:
            quoted_s = not quoted_s
        elif c == '"' and not quoted_s:
            quoted_d = not quoted_d
        else:
            result.append(c)
    if escaped:  raise ValueError('Unterminated escape sequence (\\) at end of string')
    if quoted_s: raise ValueError("Unmatched single-quote (') character in string")
    if quoted_d: raise ValueError('Unmatched double-quote (") character in string')
    return ''.join(result)
