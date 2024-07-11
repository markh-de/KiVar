#!/usr/bin/env python3

import os
import sys
import argparse
import pcbnew
try:
    from kivar_backend import Key, version, build_vardict, natural_sort_key, build_fpdict, store_fpdict, detect_current_choices, quote_str, prop_abbrev, base_prop_codes, cook_raw_string, escape_str, get_choice_dict, split_raw_str, apply_selection, pcbnew_compatibility_error
except ModuleNotFoundError:
    from .kivar_backend import Key, version, build_vardict, natural_sort_key, build_fpdict, store_fpdict, detect_current_choices, quote_str, prop_abbrev, base_prop_codes, cook_raw_string, escape_str, get_choice_dict, split_raw_str, apply_selection, pcbnew_compatibility_error

# TODO for list, allow another structure: aspect -> component -> choice (in addition to current aspect -> choice -> component)
# TODO make use of verbose options, where applicable
# TODO add option to save to a different file (create a copy)
# TODO if output to terminal, use colors for highlighting aspects, choices, matches etc.
#      (provide --no-color/-C option (or a different usual option name))
# also check all TODO notes buried in the code below!

# TODO have common help URL for both plugin and CLI? place in module?
def doc_vcs_ref():
    return f'v{version()}'

def doc_base_url():
    return f'https://doc.kivar.markh.de/{doc_vcs_ref()}/README.md'

def print_err(*args, file=sys.stderr, **kwargs):
    print(*args, file=file, **kwargs)

def load_board(in_file):
    if not os.path.isfile(in_file) or not os.access(in_file, os.R_OK):
        print_err(f'Error: "{in_file}" is not a readable file.')
        return None
    return pcbnew.LoadBoard(in_file)

def save_board(out_file, board):
    return pcbnew.SaveBoard(out_file, board)

def build_vardict_wrapper(fpdict):
    vardict, errors = build_vardict(fpdict)
    if len(errors) > 0:
        print_err(f'Errors ({len(errors)}):')
        for uuid, order, error in sorted(errors, key=lambda x: natural_sort_key(x[1])):
            print_err('    ' + error)
        return None
    if len(vardict) == 0:
        print_err(f'Error: No rule definitions found.')
        print_err(f'       Read {doc_base_url()}#usage for usage instructions.')
        return None
    return vardict

def list_command(in_file=None, long=False, prop_codes=False, detailed=False, selected=False, verbose=False):
    b = load_board(in_file)
    if b is None: return False
    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False
    if selected: sel = detect_current_choices(fpdict, vardict)
    ndict = {}
    for uuid in vardict:
        aspect = vardict[uuid][Key.ASPECT]
        if not aspect in ndict:
            ndict[aspect] = {}
        for choice in vardict[uuid][Key.BASE]:
            if not choice in ndict[aspect]:
                ndict[aspect][choice] = {}
            if detailed:
                cmp_info = []
                cmp_value = vardict[uuid][Key.BASE][choice][Key.VALUE]
                if cmp_value is not None:
                    cmp_info.append(quote_str(cmp_value))
                cmp_props = vardict[uuid][Key.BASE][choice][Key.PROPS]
                for prop_code in fpdict[uuid][Key.PROPS]:
                    if prop_code in cmp_props and cmp_props[prop_code] is not None:
                        # TODO use colored output and use green and red here!
                        if prop_codes:
                            state_text = '+' if cmp_props[prop_code] else '-'
                            cmp_info.append(f'{state_text}{prop_code}')
                        else:
                            state_text = 'Yes' if cmp_props[prop_code] else 'No'
                            cmp_info.append(f'<{prop_abbrev(prop_code)}:{state_text}>')
                ndict[aspect][choice][uuid] = ' '.join(cmp_info)
    for aspect in sorted(ndict, key=natural_sort_key):
        p_aspect = quote_str(aspect)
        if long:
            print(p_aspect)
        else:
            print(f'{p_aspect}:', end='')
        for choice in sorted(ndict[aspect], key=natural_sort_key):
            p_choice = quote_str(choice)
            if selected and sel[aspect] == choice:
                if long:
                    print(f'  + {p_choice}')
                else:
                    print(f' [{p_choice}]', end='')
            else:
                if long:
                    print(f'    {p_choice}')
                else:
                    print(f' {p_choice}', end='')
            if detailed:
                for uuid in sorted(ndict[aspect][choice], key=lambda x: natural_sort_key(fpdict[x][Key.REF])):
                    ref = fpdict[uuid][Key.REF]
                    print(f'        {ref}: {ndict[aspect][choice][uuid]}')
                    for field in sorted(vardict[uuid][Key.AUX], key=natural_sort_key):
                        f = quote_str(field)
                        v = quote_str(vardict[uuid][Key.AUX][field][choice][Key.VALUE])
                        print(f"            {f}: {v}")
                        # Future note: When properties for aux expressions are allowed, print them here
        print()
    return True

def state_command(in_file=None, all=False, query_aspect=None, verbose=False):
    b = load_board(in_file)
    if b is None: return False
    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False
    sel = detect_current_choices(fpdict, vardict)
    if query_aspect is not None:
        if all:
            print_err('Error: Options "--all" and "--query" are mutually exclusive.')
            return False
        if len(query_aspect) > 1:
            print_err(f'Error: Only one query allowed.')
            return False
        q = cook_raw_string(query_aspect[0])
        if q in sel:
            p_choice = quote_str(sel[q])
            print(p_choice)
        else:
            print_err(f"Error: No such aspect '{escape_str(q)}'.")
            return False
    else:
        for aspect in sorted(sel, key=natural_sort_key):
            choice = sel[aspect]
            if all or choice is not None:
                p_aspect = quote_str(aspect)
                p_c = '' if choice is None else quote_str(choice)
                print(f'{p_aspect}={p_c}')
    return True

def check_command(in_file=None, verbose=False):
    b = load_board(in_file)
    if b is None: return False
    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False
    sel = detect_current_choices(fpdict, vardict)
    failed = []
    for aspect in sorted(sel, key=natural_sort_key):
        choice = sel[aspect]
        # TODO if verbose: print result of each check here!
        if choice is None:
            failed.append(aspect)
    if len(failed) > 0:
        print_err(f'Check failed. No matching choice found for {len(failed)} (of {len(sel)}) aspect(s):')
        for aspect in failed:
            p_aspect = quote_str(aspect)
            print_err(f'    {p_aspect}')
        return False
    else:
        print_err(f'Check passed. All {len(sel)} aspect(s) have a matching choice.')
    return True

def set_command(in_file=None, out_file=None, force_save=False, assign=None, dry_run=False, verbose=False):
    # TODO how to handle errors? ignore failing assignments, or abort?
    #      collect errors, then print & return?
    if assign is None:
        print('Error: No assignments passed.')
        return False
    b = load_board(in_file)
    if b is None: return False
    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False
    sel = detect_current_choices(fpdict, vardict)
    choice_dict = get_choice_dict(vardict)
    for asmt in assign:
        l = split_raw_str(asmt, '=', False) # TODO: test split
        if len(l) == 2:
            aspect = cook_raw_string(l[0])
            choice = cook_raw_string(l[1])
            p_aspect = escape_str(aspect)
            p_choice = escape_str(choice)
            p_asmt = f'{p_aspect}={p_choice}'
            if aspect in sel:
                if choice in choice_dict[aspect]:
                    sel[aspect] = choice
                else:
                    print(f"Error: Assignment '{p_asmt}' failed: No such choice '{p_choice}' for aspect '{p_aspect}'.")
            else:
                print(f"Error: Assignment '{p_asmt}' failed: No such aspect '{p_aspect}'.")
        else:
            print(f"Error: Assignment '{asmt}' failed: Format error: Wrong number of '=' separators.")
    changes = apply_selection(fpdict, vardict, sel, dry_run=False)
    if verbose: # or dry_run:
        if changes:
            print_err(f'Changes ({len(changes)}):')
            for uuid, order, change in sorted(changes, key=lambda x: natural_sort_key(x[1])):
                print('    ' + change)
        else:
            print('No changes.')
    if not dry_run and (changes or force_save):
        store_fpdict(b, fpdict)
        if save_board(out_file, b):
            if verbose:
                print(f'Board saved to file "{out_file}".')
        else:
            print_err(f'Error: Failed to save board to file "{out_file}".')
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description=f"KiVar Command Line Interface ({version()})")
    # parser.add_argument("--verbose",      "-v", action="store_true", help="long output style (effect depends on command)")
    parser.add_argument("-V", "--version", action="store_true", help="print version information and exit")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="list all available aspects and choices")
    list_parser.add_argument("-s", "--selection",  action="store_true", help="mark currently matching choices")
    list_parser.add_argument("-l", "--long",       action="store_true", help="long output style")
    list_parser.add_argument("-d", "--detailed",   action="store_true", help="show component assignments (implies --long)")
    list_parser.add_argument("-c", "--prop-codes", action="store_true", help="display property codes (implies --detailed)")
#   list_parser.add_argument("-v", "--verbose",    action="store_true", help="verbose output")
    list_parser.add_argument("pcb", help="input KiCad PCB file name")

    state_parser = subparsers.add_parser("state", help="show currently matching choice for each aspect")
    state_parser.add_argument("-Q", "--query",   action="append",     help="query aspect for matching choice", metavar="aspect")
    state_parser.add_argument("-a", "--all",     action="store_true", help="list all aspects (default: list only aspects with matching choice)")
#   state_parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    state_parser.add_argument("pcb", help="input KiCad PCB file name")

    check_parser = subparsers.add_parser("check", help="check all aspects for matching choices, exit with error if check fails")
#    check_parser.add_argument("--verbose", "-v", action="store_true", help="verbose output")
    # TODO add option to check only for dedicated list of aspects
    check_parser.add_argument("pcb", help="input KiCad PCB file name")

    set_parser = subparsers.add_parser("set", help="assign choices to aspects")
    set_parser.add_argument("-A", "--assign",  action="append",     help="assign choice to aspect ('str' format: \"aspect=choice\")", metavar="str")
    set_parser.add_argument("-D", "--dry-run", action="store_true", help="only print assignments, do not really perform/save them")
    set_parser.add_argument("-o", "--output",  action="append",     help="override output file name and force saving", metavar="out_pcb")
    set_parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    set_parser.add_argument("pcb", help="input (and default output) KiCad PCB file name")

    args = parser.parse_args()
    exitcode = 0

    if args.version:
        print(f"KiVar {version()}")
        exitcode = 0
    else:
        # TODO do this check only prior to executing corresponding commands?
        compatibility_problem = pcbnew_compatibility_error()
        if compatibility_problem is not None:
            print(f'Compatibility error:\n{compatibility_problem}')
            exitcode = 3
        else:
            cmd = args.command
            in_file = args.pcb
            if cmd == "list":
                if args.prop_codes: args.detailed = True
                if args.detailed:   args.long = True
                if not list_command(in_file=in_file, long=args.long, prop_codes=args.prop_codes, detailed=args.detailed, selected=args.selection): exitcode = 1
            elif cmd == "state":
                if not state_command(in_file=in_file, all=args.all, query_aspect=args.query): exitcode = 1
            elif cmd == "check":
                if not check_command(in_file=in_file): exitcode = 1
            elif cmd == "set":
                if args.output:
                    out_file = args.output[-1]
                    force_save = True
                else:
                    out_file = in_file
                    force_save = False
                if not set_command(in_file=in_file, out_file=out_file, force_save=force_save, assign=args.assign, dry_run=args.dry_run, verbose=args.verbose): exitcode = 1
            else:
                print_err(f'This is the KiVar CLI, version {version()}.')
                parser.print_usage()
                exitcode = 2

    return exitcode

if __name__ == "__main__":
    sys.exit(main())
