#!/usr/bin/env python3

import os
import sys
import argparse

try:                        from  kivar_engine  import *
except ModuleNotFoundError: from .kivar_engine  import *
try:                        from  kivar_version import version
except ModuleNotFoundError: from .kivar_version import version

# TODO support variants
# * assigning variants
# * have a switch that forbids changing bound aspects
# * add a simple "create table" command, which simply binds all aspects (user needs to edit csv manually)
# * ... more ideas ... (CLI support may be implemented later than GUI, unsure about usage stats)

# TODO for list, allow another structure: aspect -> component -> choice (in addition to current aspect -> choice -> component)
# TODO make use of verbose options, where applicable
# also check all TODO notes buried in the code below!
# TODO have common help URL for both plugin and CLI? place in backend?

def doc_vcs_ref():
    return f'v{version()}'

def doc_base_url():
    return f'https://doc.kivar.markh.de/{doc_vcs_ref()}/README.md'

no_color = False
load_errors = None

class Msg:
    RESET = '\033[0m'
    CODES = {
        'error':   '\033[0;1;37;41m',
        'pass':    '\033[0;1;32m',
        'fail':    '\033[0;1;31m',
        'mod':     '\033[0;34m',
        'ref':     '\033[0;3;33m',
        'value':   '\033[0;1m',
        'field':   '\033[0;3;34m',
        'fvalue':  '\033[0;1m',
        'var':     '\033[0;33m',
        'avar':    '\033[0;1;37;43m',
        'bound':   '\033[0;33m',
        'aspect':  '\033[0;35m',
        'choice':  '\033[0;36m',
        'achoice': '\033[0;1;37;46m',
        'yes':     '\033[0;32m',
        'no':      '\033[0;31m'
    }

    def __init__(self, error=False):
        self.stream = sys.stderr if error else sys.stdout
        global no_color
        self.use_color = self.stream.isatty() and not no_color
        self.clear()

    def clear(self):
        self.data = ''
        self.reset()
        return self

    def text(self, text_string):
        self.data += text_string
        return self

    def color(self, color):
        if self.use_color and color in self.CODES:
            self.data += self.CODES[color]
        return self

    def reset(self):
        self.data += self.RESET
        return self

    def flush(self, end='\n'):
        self.reset()
        print(self.data, file=self.stream, end=end)
        self.clear()
        return self

    def content(self):
        self.reset()
        content = self.data
        self.clear()
        return content

class ErrMsg(Msg):
    def __init__(self, error=True):
        super().__init__(error)

    def c(self):
        self.color('error')
        return self

def sym_variant():
    return '~'

def load_board(in_file):
    if not os.path.isfile(in_file) or not os.access(in_file, os.R_OK):
        ErrMsg().c().text(f'Error: "{in_file}" is not a readable file.').flush()
        return None
    return pcbnew.LoadBoard(in_file)

def save_board(out_file, board):
    return pcbnew.SaveBoard(out_file, board)

def build_vardict_wrapper(fpdict):
    vardict, errors = build_vardict(fpdict)
    if len(errors) > 0:
        ErrMsg().c().text(f'Errors ({len(errors)}):').flush()
        for uuid, order, error in sorted(errors, key=lambda x: natural_sort_key(x[1])):
            ErrMsg().text('    ' + error).flush()
        return None
    if len(vardict) == 0:
        ErrMsg().c().text('Error: No rule definitions found.').flush()
        ErrMsg().text(f'       Read {doc_base_url()}#usage for usage instructions.').flush()
        return None
    return vardict

def load_varinfo_wrapper(in_file, vardict):
    varinfo = VariantInfo(in_file)
    errors = varinfo.read_csv(get_choice_dict(vardict))
    if not varinfo.is_loaded(): show_variants = False # if not loaded, disable variants altogether
    if len(errors) > 0:
        ErrMsg().c().text(f'Errors when loading variant table:').flush()
        for error in errors:
            ErrMsg().text('    ' + error).flush()
        return None
    return varinfo

def reorder_aspects(all_aspects, bound_aspects):
    free_aspects = [aspect for aspect in all_aspects if aspect not in bound_aspects]
    return bound_aspects + free_aspects

def list_command(in_file=None, long=False, prop_codes=False, detailed=False, selected=False, use_variants=False, only_variants=False, cust_asp_order=False):
    b = load_board(in_file)
    if b is None: return False

    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False

    if selected:
        sel = detect_current_choices(fpdict, vardict)

    if use_variants:
        varinfo = load_varinfo_wrapper(in_file, vardict)
        if varinfo is None: return False
        if not varinfo.is_loaded(): use_variants = False

    ndict = {}
    for uuid in vardict:
        aspect = vardict[uuid][Key.ASPECT]
        if not aspect in ndict:
            ndict[aspect] = {}
        for choice in vardict[uuid][Key.CMP]:
            if not choice in ndict[aspect]:
                ndict[aspect][choice] = {}
            if detailed:
                cmp_info = []
                cmp_value = vardict[uuid][Key.CMP][choice][Key.VALUE]
                if cmp_value is not None:
                    cmp_info.append(Msg().color('value').text(quote_str(cmp_value)).content())
                cmp_props = vardict[uuid][Key.CMP][choice][Key.PROPS]
                for prop_code in fpdict[uuid][Key.PROPS]:
                    if prop_code in cmp_props and cmp_props[prop_code] is not None:
                        m = Msg()
                        if prop_codes:
                            if cmp_props[prop_code]:
                                m.color('yes').text('+')
                            else:
                                m.color('no').text('-')
                            cmp_info.append(m.text(prop_code).content())
                        else:
                            m.text('<')
                            if cmp_props[prop_code]:
                                m.color('yes')
                                state_text = 'Yes'
                            else:
                                m.color('no')
                                state_text = 'No'
                            cmp_info.append(m.text(prop_abbrev(prop_code) + ':' + state_text).reset().text('>').content())
                ndict[aspect][choice][uuid] = ' '.join(cmp_info)

    all_aspects = sorted(ndict, key=natural_sort_key)
    if use_variants:
        if cust_asp_order:
            all_aspects = reorder_aspects(all_aspects, varinfo.aspects())
        if selected:
            varsel = varinfo.match_variant(sel)
        if long:
            Msg().color('var').text(sym_variant()).flush()
        else:
            Msg().color('var').text(sym_variant()).reset().text(':').flush(end='')
        for variant in varinfo.variants():
            p_var = quote_str(variant)
            if selected and variant == varsel:
                if long:
                    Msg().text('  + ').color('avar').text(p_var).flush()
                else:
                    Msg().text(' [').color('avar').text(p_var).reset().text(']').flush(end='')
            else:
                if long:
                    Msg().text('    ').color('var').text(p_var).flush()
                else:
                    Msg().text(' ').color('var').text(p_var).flush(end='')
            if detailed:
                choices = varinfo.choices()[variant]
                for index, aspect in enumerate(varinfo.aspects()):
                    Msg().text('        ').color('aspect').text(quote_str(aspect)).reset().text(': ').color('choice').text(choices[index]).flush()

        Msg().flush()

    if not only_variants:
        for aspect in all_aspects:
            p_aspect = quote_str(aspect)
            if long:
                m = Msg().color('aspect').text(p_aspect)
                if use_variants and aspect in varinfo.aspects():
                    m.color('bound').text(sym_variant())
                m.flush()
            else:
                m = Msg().color('aspect').text(p_aspect)
                if use_variants and aspect in varinfo.aspects():
                    m.color('bound').text(sym_variant())
                m.reset().text(':').flush(end='')
            for choice in sorted(ndict[aspect], key=natural_sort_key):
                p_choice = quote_str(choice)
                if selected and sel[aspect] == choice:
                    if long:
                        Msg().text('  + ').color('achoice').text(p_choice).flush()
                    else:
                        Msg().text(' [').color('achoice').text(p_choice).reset().text(']').flush(end='')
                else:
                    if long:
                        Msg().text('    ').color('choice').text(p_choice).flush()
                    else:
                        Msg().text(' ').color('choice').text(p_choice).flush(end='')
                if detailed:
                    for uuid in sorted(ndict[aspect][choice], key=lambda x: natural_sort_key(fpdict[x][Key.REF])):
                        ref = fpdict[uuid][Key.REF]
                        Msg().text('        ').color('ref').text(ref).reset().text(': ' + ndict[aspect][choice][uuid]).flush()
                        for field in sorted(vardict[uuid][Key.FLD], key=natural_sort_key):
                            f = quote_str(field)
                            variant = quote_str(vardict[uuid][Key.FLD][field][choice][Key.VALUE])
                            Msg().text('            ').color('field').text(f).reset().text(': ').color('fvalue').text(variant).flush()
                            # Future note: When properties for field scope expressions are allowed, print them here
            Msg().flush()

    return True

def state_command(in_file=None, all=False, query_aspect=None, use_variants=False, only_variants=False, cust_asp_order=False):
    b = load_board(in_file)
    if b is None: return False

    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False

    if use_variants:
        varinfo = load_varinfo_wrapper(in_file, vardict)
        if varinfo is None: return False
        if not varinfo.is_loaded(): use_variants = False

    sel = detect_current_choices(fpdict, vardict)
    if query_aspect is not None:
        choices = []
        for qa in query_aspect:
            q = cook_raw_string(qa)
            if q in sel:
                choices.append(quote_str(sel[q]))
            else:
                ErrMsg().c().text(f"Error: No such aspect '{escape_str(q)}'.").flush()
                return False
        for c in choices:
            Msg().color('choice').text(c).flush()
    else:
        if use_variants:
            varsel = varinfo.match_variant(sel)
            p_v = '' if varsel is None else quote_str(varsel)
            Msg().color('var').text(sym_variant()).reset().text('=').color('var').text(p_v).flush()

        if not only_variants:
            all_aspects = sorted(sel, key=natural_sort_key)
            if use_variants and cust_asp_order:
                all_aspects = reorder_aspects(all_aspects, varinfo.aspects())
            for aspect in all_aspects:
                choice = sel[aspect]
                if all or choice is not None:
                    p_aspect = quote_str(aspect)
                    p_c = '' if choice is None else quote_str(choice)
                    Msg().color('aspect').text(p_aspect).reset().text('=').color('choice').text(p_c).flush()

    return True

def check_command(in_file=None, variants=False, no_variants=False):
    b = load_board(in_file)
    if b is None: return False

    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False

    sel = detect_current_choices(fpdict, vardict)

    varinfo = load_varinfo_wrapper(in_file, vardict)
    if varinfo is None: return False
    if variants and not varinfo.is_loaded():
        ErrMsg().c().text("Error: No variant definitions found (omit option '--variants' to skip check).").flush()
        return False

    check_variant_match = varinfo.is_loaded() and not no_variants

    failed = []
    for aspect in sorted(sel, key=natural_sort_key):
        choice = sel[aspect]
        if choice is None:
            failed.append(aspect)

    if len(failed) > 0:
        Msg().color('fail').text('Check failed.').reset().text(f'  No matching choice found for {len(failed)} (of {len(sel)}) aspect(s):').flush()
        for aspect in failed:
            p_aspect = quote_str(aspect)
            Msg().text('    ').color('aspect').text(p_aspect).flush()
        return False

    if check_variant_match:
        var_match = varinfo.match_variant(sel)
        if var_match is None:
            Msg().color('fail').text('Check failed.').reset().text(f'  No matching variant found for the current set of aspect choices.').flush()
            return False

    Msg().color('pass').text('Check passed.').reset().text(f'  Matching {'variant and ' if check_variant_match else ''}choices found for complete set of {len(sel)} aspect(s).').flush()
    return True

def set_command(in_file=None, out_file=None, force_save=False, variant=None, assign=None, bound=False, dry_run=False, verbose=False):
    if variant is None and assign is None:
        ErrMsg().c().text('Error: No variant or aspect assignments passed.').flush()
        return False

    b = load_board(in_file)
    if b is None: return False

    fpdict = build_fpdict(b)
    vardict = build_vardict_wrapper(fpdict)
    if vardict is None: return False

    sel = detect_current_choices(fpdict, vardict)

    if variant is not None:
        varinfo = load_varinfo_wrapper(in_file, vardict)
        if varinfo is None: return False
        if varinfo.is_loaded():
            if variant not in varinfo.variants():
                ErrMsg().c().text(f"Error: Undefined variant identifier '{escape_str(variant)}'.").flush()
                return False
            else:
                choices = varinfo.choices()[variant]
                for aspect_index, aspect in enumerate(varinfo.aspects()):
                    sel[aspect] = choices[aspect_index]
        else:
            ErrMsg().c().text("Error: Cannot set variant without a valid variant definition table.").flush()
            return False

    if assign is not None:
        choice_dict = get_choice_dict(vardict)
        for asmt in assign:
            l = split_raw_str(asmt, '=', False)
            if len(l) == 2:
                aspect = cook_raw_string(l[0])
                choice = cook_raw_string(l[1])
                p_aspect = escape_str(aspect)
                p_choice = escape_str(choice)
                p_asmt = f'{p_aspect}={p_choice}'
                if aspect in sel:
                    if not (variant is not None and aspect in varinfo.aspects() and not bound):
                        if choice in choice_dict[aspect]:
                            sel[aspect] = choice
                        else:
                            ErrMsg().c().text(f"Error: Assignment '{p_asmt}' failed: No such choice '{escape_str(p_choice)}' for aspect '{escape_str(p_aspect)}'.").flush()
                            return False
                    else:
                        ErrMsg().c().text(f"Error: Overriding choices of bound aspect '{escape_str(aspect)}' is forbidden (use option '--bound' to allow).").flush()
                        return False
                else:
                    ErrMsg().c().text(f"Error: Assignment '{p_asmt}' failed: No such aspect '{escape_str(p_aspect)}'.").flush()
                    return False
            else:
                ErrMsg().c().text(f"Error: Assignment '{asmt}' failed: Format error: Wrong number of '=' separators.").flush()
                return False

    changes = apply_selection(fpdict, vardict, sel, dry_run=False)
    if verbose: # or dry_run:
        if changes:
            Msg().text(f'Changes ({len(changes)}):').flush()
            for uuid, order, change in sorted(changes, key=lambda x: natural_sort_key(x[1])):
                Msg().text('    ').color('mod').text(change).flush()
        else:
            Msg().text('No changes.').flush()

    if not dry_run and (changes or force_save):
        store_fpdict(b, fpdict)
        if save_board(out_file, b):
            if verbose:
                Msg().text(f'Board saved to file "{out_file}".').flush()
        else:
            ErrMsg().c().text(f'Error: Failed to save board to file "{out_file}".').flush()
            return False

    return True

def main():
    global no_color
    parser = argparse.ArgumentParser(description=f"KiVar Command Line Interface ({version()})")
    parser.add_argument("-n", "--no-color", action="store_true", help="suppress output coloring (default for stdout redirection)")
    parser.add_argument(      "--version",  action="store_true", help="print version information and exit")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="list all available aspects and choices")
    list_parser.add_argument("-V", "--variants",    action="store_true", help="variant information only, skip aspect list")
    list_parser.add_argument("-N", "--no-variants", action="store_true", help="suppress variant information")
    list_parser.add_argument("-O", "--std-order",   action="store_true", help="ignore aspect order from variant table")
    list_parser.add_argument("-s", "--selection",   action="store_true", help="mark currently matching choices")
    list_parser.add_argument("-l", "--long",        action="store_true", help="long output style")
    list_parser.add_argument("-d", "--detailed",    action="store_true", help="show component assignments (implies --long)")
    list_parser.add_argument("-c", "--prop-codes",  action="store_true", help="display property codes (implies --detailed)")
    list_parser.add_argument("pcb", help="input KiCad PCB file name")

    state_parser = subparsers.add_parser("state", help="show currently matching choice for each aspect")
    state_parser.add_argument("-V", "--variants",    action="store_true", help="variant information only, skip aspect list")
    state_parser.add_argument("-N", "--no-variants", action="store_true", help="suppress variant information")
    state_parser.add_argument("-O", "--std-order",   action="store_true", help="ignore aspect order from variant table")
    state_parser.add_argument("-Q", "--query",       action="append",     help="add aspect to query for matching choice", metavar="aspect")
    state_parser.add_argument("-a", "--all",         action="store_true", help="list all aspects (default: list only aspects with matching choice)")
    state_parser.add_argument("pcb", help="input KiCad PCB file name")

    check_parser = subparsers.add_parser("check", help="check variants and/or aspects for matching choices, exit with error if check fails")
    check_parser.add_argument("-V", "--variants",    action="store_true", help="fail if no variant definition table exists")
    check_parser.add_argument("-N", "--no-variants", action="store_true", help="only check aspects, not variants")
    check_parser.add_argument("pcb", help="input KiCad PCB file name")

    set_parser = subparsers.add_parser("set", help="assign choices to aspects")
    set_parser.add_argument("-V", "--variant", action="append",     help="switch to specific variant", metavar="str")
    set_parser.add_argument("-A", "--assign",  action="append",     help="assign choice to aspect ('str' format: \"aspect=choice\")", metavar="str")
    set_parser.add_argument("-b", "--bound",   action="store_true", help="allow overriding bound aspects (applied after variant)")
    set_parser.add_argument("-D", "--dry-run", action="store_true", help="only print assignments, do not really perform/save them")
    set_parser.add_argument("-o", "--output",  action="append",     help="override output file name and force saving", metavar="out_pcb")
    set_parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    set_parser.add_argument("pcb", help="input (and default output) KiCad PCB file name")

    args = parser.parse_args()
    no_color = args.no_color
    exitcode = 0

    if load_errors is not None:
        for e in load_errors: ErrMsg().c().text(e).flush()
        exitcode = 4
    elif args.version:
        Msg().text(f"KiVar {version()} (using pcbnew {pcbnew.Version()})").flush()
        exitcode = 0
    else:
        # TODO do this check only prior to executing corresponding commands?
        compatibility_problem = pcbnew_compatibility_error()
        if compatibility_problem is not None:
            ErrMsg().c().text('Compatibility error:').flush()
            ErrMsg().text(compatibility_problem).flush()
            exitcode = 3
        else:
            cmd = args.command
            if cmd == "list":
                if args.prop_codes: args.detailed = True
                if args.detailed:   args.long = True
                if args.variants and args.no_variants:
                    ErrMsg().c().text('Error: Options "--variants" and "--no-variants" are mutually exclusive.').flush()
                    exitcode = 5
                elif not list_command(in_file=args.pcb, long=args.long, prop_codes=args.prop_codes, detailed=args.detailed, selected=args.selection, use_variants=not args.no_variants, only_variants=args.variants, cust_asp_order=not args.std_order): exitcode = 1
            elif cmd == "state":
                if args.all and args.query_aspect:
                    ErrMsg().c().text('Error: Options "--all" and "--query" are mutually exclusive.').flush()
                    exitcode = 5
                elif not state_command(in_file=args.pcb, all=args.all, query_aspect=args.query, use_variants=not args.no_variants, only_variants=args.variants, cust_asp_order=not args.std_order): exitcode = 1
            elif cmd == "check":
                if not check_command(in_file=args.pcb, variants=args.variants, no_variants=args.no_variants): exitcode = 1
            elif cmd == "set":
                if args.output is not None and len(args.output) > 1:
                    ErrMsg().c().text('Error: Option "--output" cannot be used multiple times.').flush()
                    exitcode = 5
                elif args.variant is not None and len(args.variant) > 1:
                    ErrMsg().c().text('Error: Option "--variant" cannot be used multiple times.').flush()
                    exitcode = 5
                else:
                    if args.output is not None and len(args.output) == 1:
                        out_file = args.output[0]
                        force_save = True
                    else:
                        out_file = args.pcb
                        force_save = False
                    variant = None if args.variant is None else args.variant[0]
                    if not set_command(in_file=args.pcb, out_file=out_file, force_save=force_save, variant=variant, assign=args.assign, bound=args.bound, dry_run=args.dry_run, verbose=args.verbose): exitcode = 1
            else:
                Msg().text(f'This is the KiVar CLI, version {version()}.').flush()
                parser.print_usage()
                exitcode = 2

    return exitcode

try: import pcbnew
except ModuleNotFoundError as e:
    load_errors = [f"Error: The '{e.name}' Python module cannot be loaded.", "Please ensure that KiCad is installed and that your Python environment is configured to access KiCad's scripting modules."]

if __name__ == "__main__":
    sys.exit(main())
