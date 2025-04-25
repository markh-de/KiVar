import pcbnew
from os import path as os_path

from .kivar_version import version
from . import kivar_gui as gui
from . import kivar_engine as engine

DEBUG = False

class KiVarPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = f'KiVar: Switch Assembly Variants'
        self.category = 'Assembly Variants'
        self.description = 'Switch between predefined assembly variant choices'
        self.icon_file_name      = os_path.join(os_path.dirname(__file__), 'de_markh_kivar-icon-light.png')
        self.dark_icon_file_name = os_path.join(os_path.dirname(__file__), 'de_markh_kivar-icon-dark.png')
        self.show_toolbar_button = True

    def Run(self):
        if DEBUG:
            import sys
            log_file = os_path.join(os_path.dirname(__file__), 'kivar_debug.txt')
            sys.stderr = open(log_file, "w")
            sys.stdout = sys.stderr
        compatibility_problem = engine.pcbnew_compatibility_error()
        if compatibility_problem is not None:
            wx.MessageBox(message=compatibility_problem, caption=f'Compatibility Problem | KiVar {version()}', style=wx.ICON_ERROR)
            return
        board = pcbnew.GetBoard()
        fpdict = engine.build_fpdict(board)
        vardict, errors = engine.build_vardict(fpdict)
        if len(errors) > 0:
            gui.show_error_dialog(errors, board)
        elif len(vardict) == 0:
            gui.show_missing_rules_dialog(engine.legacy_expressions_found(fpdict))
        else:
            gui.show_selection_dialog(board, fpdict, vardict)

KiVarPlugin().register()
