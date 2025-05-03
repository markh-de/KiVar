import pcbnew
import wx
import os
import json

from .kivar_version import version
from . import kivar_gui as gui
from . import kivar_engine as engine

DEBUG = False
def create_icon(source_icon, cached_icon, icon_size, max_size=64):
    if not os.path.exists(cached_icon):
        try:
            image = wx.Image(source_icon, wx.BITMAP_TYPE_PNG)
            image = image.Scale(icon_size, icon_size, wx.IMAGE_QUALITY_HIGH)
            image.SaveFile(cached_icon, wx.BITMAP_TYPE_PNG)
        except (PermissionError, FileNotFoundError):
            pass

def get_icon_size():
    icon_size = 24 # default size
    scale = wx.Display().GetScaleFactor() # use default display
    version_major_minor = pcbnew.GetMajorMinorVersion()
    config_dir = None
    manual_home = os.environ.get("KICAD_CONFIG_HOME")
    if manual_home is not None and manual_home != '':
        config_dir = manual_home
    else:
        platform = wx.Platform
        if platform == '__WXGTK__':
            config_home = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
            config_dir = os.path.join(config_home, 'kicad')
        elif platform == '__WXMAC__':
            config_home = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), 'Library', 'Preferences'))
            config_dir = os.path.join(config_home, 'kicad')
        elif platform == '__WXMSW__':
            appdata = os.environ.get('appdata', os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming'))
            config_dir = os.path.join(appdata, 'kicad')
    if config_dir is not None:
        config_file = os.path.join(config_dir, version_major_minor, 'kicad_common.json')
        with open(config_file, 'r') as f:
            config = json.load(f)
            icon_size = config.get("appearance", {}).get("toolbar_icon_size", icon_size)
    return int(icon_size * scale)

class KiVarPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        plugin_dir = os.path.dirname(__file__)

        if DEBUG:
            import sys
            log_file = os.path.join(plugin_dir, 'kivar_debug.txt')
            sys.stderr = open(log_file, "w")
            sys.stdout = sys.stderr

        icon_size = get_icon_size()
        icon_source_light = os.path.join(plugin_dir, 'kivar_icon_light.png')
        icon_source_dark  = os.path.join(plugin_dir, 'kivar_icon_dark.png')
        icon_scaled_light = os.path.join(plugin_dir, f'kivar_icon_light_{icon_size}.png')
        icon_scaled_dark  = os.path.join(plugin_dir, f'kivar_icon_dark_{icon_size}.png')
        create_icon(icon_source_light, icon_scaled_light, icon_size)
        create_icon(icon_source_dark,  icon_scaled_dark,  icon_size)

        self.name                = 'KiVar: Switch Assembly Variants'
        self.category            = 'Assembly Variants'
        self.description         = 'Switch between predefined assembly variant choices'
        self.icon_file_name      = icon_scaled_light
        self.dark_icon_file_name = icon_scaled_dark
        self.show_toolbar_button = True

    def Run(self):
        if DEBUG:
            import sys
            log_file = os.path.join(os.path.dirname(__file__), 'kivar_debug.txt')
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
