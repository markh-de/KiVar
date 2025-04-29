# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6-dirty)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from .kivar_gui_custom import MenuButton
from .kivar_gui_custom import PcbItemListBox
import wx
import wx.xrc
import wx.adv

###########################################################################
## Class VariantDialog
###########################################################################

class VariantDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Variant Selection", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER, name = u"kivar_sel" )

        self.SetSizeHints( wx.Size( 700,350 ), wx.DefaultSize )

        sz_main = wx.BoxSizer( wx.VERTICAL )

        sz_main.SetMinSize( wx.Size( 700,350 ) )
        sz_var_hor = wx.BoxSizer( wx.HORIZONTAL )

        sz_var_hor.SetMinSize( wx.Size( 700,100 ) )
        sz_var_left = wx.BoxSizer( wx.VERTICAL )

        sz_var_left.SetMinSize( wx.Size( 300,100 ) )
        sz_variant = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_variant = wx.StaticText( self, wx.ID_ANY, u"Variant:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_variant.Wrap( -1 )

        sz_variant.Add( self.lbl_variant, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        chc_variantChoices = []
        self.chc_variant = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, chc_variantChoices, 0 )
        self.chc_variant.SetSelection( 0 )
        sz_variant.Add( self.chc_variant, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, 5 )

        self.bt_var_menu = MenuButton( self, wx.ID_ANY, u"︙", wx.DefaultPosition, wx.Size( 32,-1 ), wx.BU_EXACTFIT )
        self.bt_var_menu.SetToolTip( u"Manage variant definitions" )
        self.bt_var_menu.SetMinSize( wx.Size( 32,-1 ) )
        self.bt_var_menu.SetMaxSize( wx.Size( 32,-1 ) )

        sz_variant.Add( self.bt_var_menu, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, 5 )


        sz_var_left.Add( sz_variant, 0, wx.BOTTOM|wx.EXPAND|wx.TOP, 5 )

        sbox_bound = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Bound Aspects" ), wx.VERTICAL )

        self.scw_bound = wx.ScrolledWindow( sbox_bound.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
        self.scw_bound.SetScrollRate( 8, 8 )
        sz_bound = wx.BoxSizer( wx.VERTICAL )

        self.pnl_bound = wx.Panel( self.scw_bound, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        fgsz_bound = wx.FlexGridSizer( 0, 3, 5, 5 )
        fgsz_bound.AddGrowableCol( 0, 1 )
        fgsz_bound.AddGrowableCol( 2, 1 )
        fgsz_bound.SetFlexibleDirection( wx.BOTH )
        fgsz_bound.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        self.pnl_bound.SetSizer( fgsz_bound )
        self.pnl_bound.Layout()
        fgsz_bound.Fit( self.pnl_bound )
        sz_bound.Add( self.pnl_bound, 1, wx.EXPAND |wx.ALL, 5 )


        self.scw_bound.SetSizer( sz_bound )
        self.scw_bound.Layout()
        sz_bound.Fit( self.scw_bound )
        sbox_bound.Add( self.scw_bound, 1, wx.EXPAND |wx.ALL, 5 )


        sz_var_left.Add( sbox_bound, 1, wx.EXPAND, 5 )


        sz_var_hor.Add( sz_var_left, 1, wx.EXPAND, 6 )


        sz_var_hor.Add( ( 12, 0), 0, 0, 5 )

        sz_var_right = wx.BoxSizer( wx.VERTICAL )

        sz_var_right.SetMinSize( wx.Size( 300,100 ) )
        sbox_free = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Free Aspects" ), wx.VERTICAL )

        self.scw_free = wx.ScrolledWindow( sbox_free.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
        self.scw_free.SetScrollRate( 8, 8 )
        sz_free = wx.BoxSizer( wx.VERTICAL )

        self.pnl_free = wx.Panel( self.scw_free, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        fgsz_free = wx.FlexGridSizer( 0, 3, 5, 5 )
        fgsz_free.AddGrowableCol( 0, 1 )
        fgsz_free.AddGrowableCol( 2, 1 )
        fgsz_free.SetFlexibleDirection( wx.BOTH )
        fgsz_free.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )


        self.pnl_free.SetSizer( fgsz_free )
        self.pnl_free.Layout()
        fgsz_free.Fit( self.pnl_free )
        sz_free.Add( self.pnl_free, 1, wx.ALL|wx.EXPAND, 5 )


        self.scw_free.SetSizer( sz_free )
        self.scw_free.Layout()
        sz_free.Fit( self.scw_free )
        sbox_free.Add( self.scw_free, 1, wx.ALL|wx.EXPAND, 5 )


        sz_var_right.Add( sbox_free, 1, wx.EXPAND, 5 )


        sz_var_hor.Add( sz_var_right, 1, wx.EXPAND, 6 )


        sz_main.Add( sz_var_hor, 12, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 10 )

        sz_changes = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Changes to Be Applied" ), wx.VERTICAL )

        sz_changes.SetMinSize( wx.Size( 700,100 ) )
        lbx_changesChoices = []
        self.lbx_changes = PcbItemListBox( sz_changes.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lbx_changesChoices, wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_SINGLE )
        self.lbx_changes.SetMinSize( wx.Size( 700,100 ) )

        sz_changes.Add( self.lbx_changes, 1, wx.ALL|wx.EXPAND, 5 )


        sz_main.Add( sz_changes, 10, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 10 )

        sz_bottom = wx.BoxSizer( wx.HORIZONTAL )

        self.link_help = wx.adv.HyperlinkCtrl( self, wx.ID_ANY, u"Help ...", u"https://kivar.markh.de", wx.DefaultPosition, wx.DefaultSize, wx.adv.HL_DEFAULT_STYLE )
        sz_bottom.Add( self.link_help, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5 )


        sz_bottom.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        sdbsz = wx.StdDialogButtonSizer()
        self.sdbszOK = wx.Button( self, wx.ID_OK )
        sdbsz.AddButton( self.sdbszOK )
        self.sdbszCancel = wx.Button( self, wx.ID_CANCEL )
        sdbsz.AddButton( self.sdbszCancel )
        sdbsz.Realize()

        sz_bottom.Add( sdbsz, 0, wx.ALIGN_CENTER_VERTICAL, 5 )


        sz_main.Add( sz_bottom, 0, wx.BOTTOM|wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        self.SetSizer( sz_main )
        self.Layout()
        sz_main.Fit( self )
        self.menu_var = wx.Menu()
        self.mi_create_defs = wx.MenuItem( self.menu_var, wx.ID_ANY, u"&Create Definition Table File...", wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_var.Append( self.mi_create_defs )

        self.mi_add_def = wx.MenuItem( self.menu_var, wx.ID_ANY, u"&Add New Definition...", wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_var.Append( self.mi_add_def )

        self.mi_edit_defs = wx.MenuItem( self.menu_var, wx.ID_ANY, u"&Edit Definition Table...", wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_var.Append( self.mi_edit_defs )

        self.mi_del_def = wx.MenuItem( self.menu_var, wx.ID_ANY, u"&Delete Selected Definition...", wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_var.Append( self.mi_del_def )

        self.menu_var.AppendSeparator()

        self.mi_reload = wx.MenuItem( self.menu_var, wx.ID_ANY, u"&Reload and Reset", wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_var.Append( self.mi_reload )



        self.Centre( wx.BOTH )

        # Connect Events
        self.chc_variant.Bind( wx.EVT_CHOICE, self.on_variant_change )
        self.Bind( wx.EVT_MENU, self.on_mi_create_defs, id = self.mi_create_defs.GetId() )
        self.Bind( wx.EVT_MENU, self.on_mi_add_def, id = self.mi_add_def.GetId() )
        self.Bind( wx.EVT_MENU, self.on_mi_edit_defs, id = self.mi_edit_defs.GetId() )
        self.Bind( wx.EVT_MENU, self.on_mi_del_def, id = self.mi_del_def.GetId() )
        self.Bind( wx.EVT_MENU, self.on_mi_reload, id = self.mi_reload.GetId() )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_variant_change( self, event ):
        event.Skip()

    def on_mi_create_defs( self, event ):
        event.Skip()

    def on_mi_add_def( self, event ):
        event.Skip()

    def on_mi_edit_defs( self, event ):
        event.Skip()

    def on_mi_del_def( self, event ):
        event.Skip()

    def on_mi_reload( self, event ):
        event.Skip()


###########################################################################
## Class MissingRulesDialog
###########################################################################

class MissingRulesDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Missing Rule Definitions", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        sz_main = wx.BoxSizer( wx.VERTICAL )

        self.txt_info = wx.StaticText( self, wx.ID_ANY, u"KiVar could not find any valid rule definitions.\n\nPlease consult the KiVar documentation to learn how to\nassign variation rules to symbols or footprints:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_info.SetLabelMarkup( u"KiVar could not find any valid rule definitions.\n\nPlease consult the KiVar documentation to learn how to\nassign variation rules to symbols or footprints:" )
        self.txt_info.Wrap( -1 )

        sz_main.Add( self.txt_info, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 20 )

        self.link_help = wx.adv.HyperlinkCtrl( self, wx.ID_ANY, u"...", wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.adv.HL_DEFAULT_STYLE )
        sz_main.Add( self.link_help, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 5 )

        self.btn_close = wx.Button( self, wx.ID_OK, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
        sz_main.Add( self.btn_close, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 20 )


        self.SetSizer( sz_main )
        self.Layout()
        sz_main.Fit( self )

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class ErrorListDialog
###########################################################################

class ErrorListDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Initialization Failure", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER )

        self.SetSizeHints( wx.Size( 400,200 ), wx.DefaultSize )

        sz_main = wx.BoxSizer( wx.VERTICAL )

        sz_errors = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Errors" ), wx.VERTICAL )

        lbx_errorsChoices = []
        self.lbx_errors = PcbItemListBox( sz_errors.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lbx_errorsChoices, wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_SINGLE )
        sz_errors.Add( self.lbx_errors, 1, wx.ALL|wx.EXPAND, 5 )


        sz_main.Add( sz_errors, 1, wx.ALL|wx.EXPAND, 10 )

        sz_bottom = wx.BoxSizer( wx.HORIZONTAL )

        self.link_help = wx.adv.HyperlinkCtrl( self, wx.ID_ANY, u"Usage Guide", u"...", wx.DefaultPosition, wx.DefaultSize, wx.adv.HL_DEFAULT_STYLE )
        sz_bottom.Add( self.link_help, 0, wx.ALIGN_CENTER_VERTICAL, 5 )


        sz_bottom.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.btn_close = wx.Button( self, wx.ID_OK, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
        sz_bottom.Add( self.btn_close, 0, wx.ALIGN_CENTER_VERTICAL, 5 )


        sz_main.Add( sz_bottom, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10 )


        sz_main.Add( ( 0, 5), 0, 0, 5 )


        self.SetSizer( sz_main )
        self.Layout()
        sz_main.Fit( self )

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class CreateTableDialog
###########################################################################

class CreateTableDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Create Variant Definition Table", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        sz_main = wx.BoxSizer( wx.VERTICAL )

        self.txt_intro = wx.StaticText( self, wx.ID_ANY, u"This will create a <b>Variant Definition Table</b> binding the following aspects:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_intro.SetLabelMarkup( u"This will create a <b>Variant Definition Table</b> binding the following aspects:" )
        self.txt_intro.Wrap( 1 )

        sz_main.Add( self.txt_intro, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 12 )

        self.txt_aspects = wx.StaticText( self, wx.ID_ANY, u"...", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_aspects.Wrap( -1 )

        sz_main.Add( self.txt_aspects, 0, wx.ALIGN_CENTER|wx.ALL, 12 )

        self.txt_explain_sel = wx.StaticText( self, wx.ID_ANY, u"<i>Aspect binding:</i>  To <b>bind</b> aspects to the variant definitions, assign the desired <i>specific choices</i>\nto them in the main dialog.  To keep aspects as <b>free</b>, select the <i>unspecified</i> choice for them.\n\nIf you are not yet satisfied with the above bindings, go back to the main dialog and make the\nappropriate selections now.\n\n<i>Tip:</i> You can customize the display order of aspects and variants by modifying their order in\nthe variants table file (use the <i>'Edit Definition Table...'</i> option).", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_explain_sel.SetLabelMarkup( u"<i>Aspect binding:</i>  To <b>bind</b> aspects to the variant definitions, assign the desired <i>specific choices</i>\nto them in the main dialog.  To keep aspects as <b>free</b>, select the <i>unspecified</i> choice for them.\n\nIf you are not yet satisfied with the above bindings, go back to the main dialog and make the\nappropriate selections now.\n\n<i>Tip:</i> You can customize the display order of aspects and variants by modifying their order in\nthe variants table file (use the <i>'Edit Definition Table...'</i> option)." )
        self.txt_explain_sel.Wrap( -1 )

        sz_main.Add( self.txt_explain_sel, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 12 )

        sz_varid = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_varid = wx.StaticText( self, wx.ID_ANY, u"Initial variant identifier:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_varid.Wrap( -1 )

        sz_varid.Add( self.lbl_varid, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

        self.txc_varid = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
        sz_varid.Add( self.txc_varid, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        sz_main.Add( sz_varid, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL, 12 )

        sdbsz = wx.StdDialogButtonSizer()
        self.sdbszOK = wx.Button( self, wx.ID_OK )
        sdbsz.AddButton( self.sdbszOK )
        self.sdbszCancel = wx.Button( self, wx.ID_CANCEL )
        sdbsz.AddButton( self.sdbszCancel )
        sdbsz.Realize()

        sz_main.Add( sdbsz, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        self.SetSizer( sz_main )
        self.Layout()
        sz_main.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.txc_varid.Bind( wx.EVT_TEXT_ENTER, self.on_confirm )
        self.sdbszOK.Bind( wx.EVT_BUTTON, self.on_confirm )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_confirm( self, event ):
        event.Skip()



###########################################################################
## Class AddVariantDialog
###########################################################################

class AddVariantDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Add Variant Definition", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        sz_main = wx.BoxSizer( wx.VERTICAL )

        self.txt_intro = wx.StaticText( self, wx.ID_ANY, u"This will add a <b>Variant Definition</b> with the following assignments:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_intro.SetLabelMarkup( u"This will add a <b>Variant Definition</b> with the following assignments:" )
        self.txt_intro.Wrap( 1 )

        sz_main.Add( self.txt_intro, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 12 )

        self.txt_aspects = wx.StaticText( self, wx.ID_ANY, u"...", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_aspects.Wrap( -1 )

        sz_main.Add( self.txt_aspects, 0, wx.ALIGN_CENTER|wx.ALL, 12 )

        self.txt_explain_sel = wx.StaticText( self, wx.ID_ANY, u"If you are not yet satisfied with the above assignments, go back\nto the main dialog and make the appropriate selections now.", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_explain_sel.SetLabelMarkup( u"If you are not yet satisfied with the above assignments, go back\nto the main dialog and make the appropriate selections now." )
        self.txt_explain_sel.Wrap( -1 )

        sz_main.Add( self.txt_explain_sel, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 12 )

        sz_varid = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_varid = wx.StaticText( self, wx.ID_ANY, u"New variant identifier:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_varid.Wrap( -1 )

        sz_varid.Add( self.lbl_varid, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

        self.txc_varid = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
        sz_varid.Add( self.txc_varid, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        sz_main.Add( sz_varid, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL, 12 )

        sdbsz = wx.StdDialogButtonSizer()
        self.sdbszOK = wx.Button( self, wx.ID_OK )
        sdbsz.AddButton( self.sdbszOK )
        self.sdbszCancel = wx.Button( self, wx.ID_CANCEL )
        sdbsz.AddButton( self.sdbszCancel )
        sdbsz.Realize()

        sz_main.Add( sdbsz, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        self.SetSizer( sz_main )
        self.Layout()
        sz_main.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.txc_varid.Bind( wx.EVT_TEXT_ENTER, self.on_confirm )
        self.sdbszOK.Bind( wx.EVT_BUTTON, self.on_confirm )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_confirm( self, event ):
        event.Skip()



