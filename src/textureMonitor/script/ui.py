"""
Author: Liam Collod
Last Modified: 16/01/2020

Python 2.7 only
Katana script, tested on 3.6v4
"""
import os
import re
import logging
from functools import partial

from Katana import NodegraphAPI, UI4, KatanaFile

from PyQt5 import QtWidgets, QtCore, QtGui

from .utilities import (return_children_textures, open_file_inexplorer)
from .exceptions import (DisplayError, CustomWarning, raise_dialog, TreeWidgetItemError)
from .constants import (TREEW_DATA, DataRole, LOCKED_LIST, RESOURCES_LOCATION, ENABLE_RETEX)

from . import constants

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

""" --------------------------------------------------------------------------------------------------------------------
UI RESOURCES 
"""


class Colors:
    """
    Base colors used through the UI
    """
    blue_color = (134, 145, 179)  # color for expression
    red_color = (215, 94, 102)  # color for non existing path
    child = (150, 150, 150)  # color for child items
    text_basic = (179, 179, 179)  # default color for text
    text_disable = (100, 100, 100)


# Font loading
_font_JetBrain_Regular_path = os.path.join(RESOURCES_LOCATION, "fonts", "JetBrainsMonoNL-Medium.ttf")
_id = QtGui.QFontDatabase.addApplicationFont(_font_JetBrain_Regular_path)
FONT_JetBrainNL_Medium = QtGui.QFontDatabase.applicationFontFamilies(_id)[0]
logger.debug("[TextureMonitor Loading] FONT ID: {}".format(FONT_JetBrainNL_Medium))


class Icons:
    """
    Hold the file path for the icons used in the UI
    """
    # Base location of the file
    _base_location = os.path.join(RESOURCES_LOCATION, 'icons', 'texture_monitor')

    refresh = os.path.join(_base_location, "refresh.png")
    expand = os.path.join(_base_location, "expand.png")
    collapse = os.path.join(_base_location, "collapse.png")
    edit_node = os.path.join(_base_location, "edit_node.png")
    retex_bake = os.path.join(_base_location, "retex_bake.png")
    retex_remove = os.path.join(_base_location, "retex_remove.png")
    open_folder = os.path.join(_base_location, "open_folder.png")
    searchreplace = os.path.join(_base_location, "searchreplace.png")

    check_error = os.path.join(_base_location, "retex_remove.png")
    check_warning = os.path.join(_base_location, "retex_warning.png")
    check_ok = os.path.join(_base_location, "retex_bake.png")


def get_icon_for_qitem(qitem):
    """ Return an icon path corresponding to the data of the QTreeWidgetItem

    Args:
        qitem (QtWidgets.QTreeWidgetItem):

    Returns:
        str: file path

    Raises:
        CustomWarning: if no corresponding icon found
    """
    retex = qitem.data(TREEW_DATA["enginetex_baked"]["column"], QtCore.Qt.UserRole)  # int from DataRole

    if retex == DataRole.all_enginetex:
        return Icons.check_ok
    if retex == DataRole.some_enginetex:
        return Icons.check_warning
    if retex == DataRole.no_enginetex:
        return Icons.check_error

    raise CustomWarning("No corresponding icon found for qitem {}".format(qitem))


""" -------------------------------------------------------------------------------------------------------------------- 
UI Creation
"""


class TextureMonitorUI(UI4.Tabs.BaseTab):

    size_toolbar_icon = 18
    size_tw_icons = (16, 16)  # w,h
    size_contextmenu_icons = 12

    def __init__(self, parent):
        super(TextureMonitorUI, self).__init__(parent)

        logger.info("// {} v{} Launched with render engine: {}".format(constants.APPNAME, constants.VERSION,
                                                                       str(constants.RENDER_ENGINE.__name__).split(
                                                                           ".")[-1]))

        self.parent_window = self.parentWidget().parentWidget()  # UI4.App.Layouts.FloatingLayoutWidget
        self.parent_window.setMinimumWidth(constants.UI_WIDTH)

        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.modify_widgets()
        self.setup_connections()

        self.populate_treewidget()

    def create_widgets(self):

        self.main_widget = QtWidgets.QWidget()

        self.cbb_renderengine = QtWidgets.QComboBox()
        self.cbb_renderengine.addItems(constants.RENDER_ENGINES_AVAILABLE)
        self.cbb_renderengine.setCurrentText(str(constants.RENDER_ENGINE.__name__).split(".")[-1])

        self.grp_tree = QtWidgets.QGroupBox("ALL Textures in scene")

        """ Toolbar above the treewidget """
        self.toolbar_tw = QtWidgets.QToolBar()
        # Btn 01
        pixmap_refresh = QtGui.QPixmap(Icons.refresh
                                       ).scaled(self.size_toolbar_icon,
                                                self.size_toolbar_icon,
                                                transformMode=QtCore.Qt.SmoothTransformation)
        self.btn_toolbar_refresh = UI4.Widgets.ToolbarButton("Refresh", self, pixmap_refresh)
        self.toolbar_tw.addWidget(self.btn_toolbar_refresh)
        # Btn 02
        pixmap_expand = QtGui.QPixmap(Icons.expand
                                      ).scaled(self.size_toolbar_icon,
                                               self.size_toolbar_icon,
                                               transformMode=QtCore.Qt.SmoothTransformation)
        self.btn_toolbar_expand = UI4.Widgets.ToolbarButton("Expand All", self, pixmap_expand)
        self.toolbar_tw.addWidget(self.btn_toolbar_expand)
        # Btn 03
        pixmap_collapse = QtGui.QPixmap(Icons.collapse
                                        ).scaled(self.size_toolbar_icon,
                                                 self.size_toolbar_icon,
                                                 transformMode=QtCore.Qt.SmoothTransformation)
        self.btn_toolbar_collapse = UI4.Widgets.ToolbarButton("Collapse All", self, pixmap_collapse)
        self.toolbar_tw.addWidget(self.btn_toolbar_collapse)
        # end toolbar

        # search and replace
        self.chkbox_sr_expr = QtWidgets.QCheckBox('Ignore Expressions')
        self.le_sr_l= QtWidgets.QLineEdit()
        self.le_sr_r= QtWidgets.QLineEdit()
        pixmap_searchreplace = QtGui.QPixmap(Icons.searchreplace
                                             ).scaled(self.size_toolbar_icon,
                                                      self.size_toolbar_icon,
                                                      transformMode=QtCore.Qt.SmoothTransformation)
        self.btn_sr_apply = UI4.Widgets.ToolbarButton("Apply Replace", self, pixmap_searchreplace)

        self.treewidget = QtWidgets.QTreeWidget()
        self.header_treeview = self.treewidget.header()

    def create_layouts(self):
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.lyt_top = QtWidgets.QHBoxLayout()
        self.lyt_treegroup = QtWidgets.QVBoxLayout(self.grp_tree)
        self.lyt_toolbar_top = QtWidgets.QHBoxLayout()

    def add_widgets_to_layouts(self):
        # set the window global layout
        self.setLayout(self.main_layout)
        self.main_layout.addLayout(self.lyt_top)
        self.main_layout.addWidget(self.grp_tree)

        self.lyt_top.addWidget(self.cbb_renderengine)
        self.lyt_treegroup.addLayout(self.lyt_toolbar_top)
        self.lyt_treegroup.addWidget(self.treewidget)
        self.lyt_toolbar_top.addWidget(self.toolbar_tw)
        self.lyt_toolbar_top.addWidget(self.chkbox_sr_expr)
        self.lyt_toolbar_top.addWidget(self.le_sr_l)
        self.lyt_toolbar_top.addWidget(self.le_sr_r)
        self.lyt_toolbar_top.addWidget(self.btn_sr_apply)

    def modify_widgets(self):
        self.main_widget.setMinimumWidth(850)

        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(4)

        self.lyt_top.insertStretch(1, 3)
        self.lyt_treegroup.setContentsMargins(5, 5, 5, 5)
        self.lyt_toolbar_top.insertStretch(1, 3)

        self.cbb_renderengine.setMinimumWidth(90)
        self.toolbar_tw.setIconSize(QtCore.QSize(self.size_toolbar_icon, self.size_toolbar_icon))
        self.toolbar_tw.setStyleSheet("border: none;")
        self.btn_toolbar_refresh.setMaximumSize(self.size_toolbar_icon, self.size_toolbar_icon)
        self.btn_toolbar_expand.setMaximumSize(self.size_toolbar_icon, self.size_toolbar_icon)
        self.btn_toolbar_collapse.setMaximumSize(self.size_toolbar_icon, self.size_toolbar_icon)

        self.chkbox_sr_expr.setChecked(True)
        self.chkbox_sr_expr.setToolTip('If not checked,  path parameter computed through expression will be'
                                       ' set to constant')
        self.chkbox_sr_expr.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_sr_l.setMinimumWidth(150)
        self.le_sr_l.setPlaceholderText("Search")
        self.le_sr_r.setMinimumWidth(150)
        self.le_sr_r.setPlaceholderText("Replace")
        self.btn_sr_apply.setMaximumSize(self.size_toolbar_icon, self.size_toolbar_icon)

        # Treewidget
        self.treewidget.setHeaderHidden(False)
        # use the dict to determine which column should be visible
        header_labels = []
        for keys, data_dict in TREEW_DATA.items():
            if data_dict["visible"]:
                header_labels.append(data_dict["pretty_name"])
        self.treewidget.setHeaderLabels(header_labels)

        self.treewidget.setColumnWidth(0, constants.UI_WIDTH - 80)

        self.treewidget.setAlternatingRowColors(True)
        self.treewidget.setSortingEnabled(True)
        self.treewidget.setItemsExpandable(True)
        self.treewidget.setRootIsDecorated(True)
        self.treewidget.setIndentation(15)
        self.treewidget.setUniformRowHeights(True)
        self.treewidget.setMinimumHeight(50)
        self.treewidget.setIconSize(QtCore.QSize(35, 35))
        self.header_treeview.setMinimumSectionSize(40)
        # self.treewidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # self.treewidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def setup_connections(self):
        self.cbb_renderengine.currentTextChanged.connect(self.change_renderengine)
        self.btn_toolbar_refresh.clicked.connect(self.populate_treewidget)
        self.btn_toolbar_expand.clicked.connect(self.treewidget.expandAll)
        self.btn_toolbar_collapse.clicked.connect(self.treewidget.collapseAll)

        self.treewidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treewidget.customContextMenuRequested[QtCore.QPoint].connect(self.tw_context_menu)
        self.btn_sr_apply.clicked.connect(self.search_n_replace)

    """ ----------------------------------------------------------------------------------------------------------------
    API methods 
    """

    def change_renderengine(self):
        re_value = self.cbb_renderengine.currentText()
        # safety check
        if re_value not in constants.RENDER_ENGINES_AVAILABLE:
            logger.error("[Re change]: given render engine {} deson't seems to be supported".format(re_value))
        try:
            constants.RENDER_ENGINE = eval("constants.render_engine.{}".format(re_value))
            logger.info("[Re change]: Render engine changed to {}".format(re_value))
        except Exception as excp:
            logger.error("[Re change]: Cannot change render engine to {}: {}".format(re_value, excp))

        self.populate_treewidget()
        return

    def tw_context_menu(self, point):
        """ Create a context menu at the given point
        Render engine agnostic

        Args:
            point(QtCore.QPoint):

        Returns:
            bool: True if created
        """
        # Infos about the node selected.
        index = self.treewidget.indexAt(point)
        if not index.isValid():
            return False

        item_sel = self.treewidget.selectedItems()

        # Building menu
        menu = QtWidgets.QMenu(self)

        if not len(item_sel) > 1:
            act_edit = menu.addAction("Select and Edit the Node")
            act_edit.triggered.connect(partial(self.qitem_edit_ktnnode, item_sel[0]))
            act_edit.setIcon(QtGui.QIcon(QtGui.QPixmap(Icons.edit_node).scaled(6,
                                                                               6,
                                                                               transformMode=QtCore.Qt.SmoothTransformation)))

            path2open = os.path.dirname(item_sel[0].data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole))
            act_open = menu.addAction("Open the location in Explorer")
            act_open.triggered.connect(partial(open_file_inexplorer, path2open))
            act_open.setIcon(QtGui.QIcon(QtGui.QPixmap(Icons.open_folder).scaled(self.size_contextmenu_icons,
                                                                                 self.size_contextmenu_icons,
                                                                                 transformMode=QtCore.Qt.SmoothTransformation)))

            menu.addSeparator()

        act_expr = menu.addAction("Remove Expression")
        act_expr.triggered.connect(partial(self.qitem_remove_expression, item_sel))

        if ENABLE_RETEX:
            if constants.RENDER_ENGINE.support_re_baking:
                act_retex = menu.addAction("Bake the {} for selection".format(constants.RENDER_ENGINE.re_tex_ext))
                act_retex.triggered.connect(partial(self.bake_selection2retex, item_sel))
                act_retex.setIcon(QtGui.QIcon(QtGui.QPixmap(Icons.retex_bake).scaled(self.size_contextmenu_icons,
                                                                                     self.size_contextmenu_icons,
                                                                                     transformMode=QtCore.Qt.SmoothTransformation)))

                act_retex = menu.addAction("Bake ALL the {} ".format(constants.RENDER_ENGINE.re_tex_ext))
                act_retex.triggered.connect(partial(self.bake_selection2retex, '_', True))
                act_retex.setIcon(QtGui.QIcon(QtGui.QPixmap(Icons.retex_bake).scaled(self.size_contextmenu_icons,
                                                                                     self.size_contextmenu_icons,
                                                                                     transformMode=QtCore.Qt.SmoothTransformation)))

            act_del_retex = menu.addAction("Delete the {} for selection".format(constants.RENDER_ENGINE.re_tex_ext))
            act_del_retex.triggered.connect(partial(self.qitem_delete_retex, item_sel))
            act_del_retex.setIcon(QtGui.QIcon(QtGui.QPixmap(Icons.retex_remove).scaled(self.size_contextmenu_icons,
                                                                                       self.size_contextmenu_icons,
                                                                                       transformMode=QtCore.Qt.SmoothTransformation)))

        menu.exec_(QtGui.QCursor.pos())
        return True

    def qitem_edit_ktnnode(self, qitem):
        """ Put the katana node linked to the given qitem in edit mode

        Args:
            qitem(QtWidgets.QTreeWidgetItem):

        Returns:
            Katana Node edited
        """
        ktn_node = qitem.data(TREEW_DATA["katana_node"]["column"], QtCore.Qt.UserRole)
        NodegraphAPI.SetNodeEdited(ktn_node, edited=True, exclusive=True)  # edit only the given node
        return ktn_node

    def qitem_remove_expression(self, qitems):
        """ Remove the expression if one is used on the path_parameter of the node linked to the given qitem(s)

        Args:
            qitems(QtWidgets.QTreeWidgetItem):

        Returns:

        """
        # Ensure qitem is an iterable
        try:
            iter(qitems)
        except TypeError:
            qitems = [qitems]

        for qitem in qitems:
            file_param = qitem.data(TREEW_DATA["path_parameter"]["column"], QtCore.Qt.UserRole)

            qitem_filepath = qitem.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
            if qitem_filepath in LOCKED_LIST:
                continue

            if file_param.isExpression():
                file_param.setExpressionFlag(False)
                continue

        # Update the treewidget
        self.tw_detect_expression()

    def qitem_return_filepaths(self, qitem):
        """ Mostly for baking

        Args:
            qitem(QtWidgets.QTreeWidgetItems):

        Returns:
            list: list of file_paths associated with the given qitem
        """
        files2bake = []
        qitem_child_count = qitem.childCount()
        if qitem_child_count:
            # iterate through every child
            for index in range(qitem_child_count):
                qsubitem = qitem.child(index)
                qsubitem_path = qsubitem.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
                files2bake.append(qsubitem_path)
        else:
            qitem_path = qitem.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
            files2bake.append(qitem_path)

        return files2bake

    def qitem_delete_retex(self, qitems_selected):
        """ Delete the render engine texture corresponding to the given items
        Render Engine agnostic

        Args:
            qitems_selected(list): list of QtWidgets.QTreeWidgetItems

        Returns:
            None
        """
        if not isinstance(qitems_selected, list):
            if not isinstance(qitems_selected, tuple):
                raise ValueError("qitems_selected submitted are not list/tuple but {}: {}".format(type(qitems_selected),
                                                                                                  qitems_selected))

        files2delete_retex = []
        for qitem in qitems_selected:
            files2delete_retex += self.qitem_return_filepaths(qitem=qitem)

        retex2delete = []
        for retex_file in files2delete_retex:
            retex = constants.RENDER_ENGINE.return_retex_from_path(retex_file)
            if os.path.exists(retex):
                retex2delete.append(retex)

        error_dict = {}
        for retex in retex2delete:  # all the retex exists as they always been verified just above
            try:
                os.remove(retex)
            except Exception as excp:
                error_dict[retex] = excp

        logger.info("retex removed: {}, with errors: {}".format(retex2delete, error_dict))
        num_total = len(retex2delete)
        num_error = len(error_dict)
        num_processed = num_total - num_error
        message = " Deleted {}/{} {} \n  - {}errors: {}".format(num_processed,
                                                                num_total,
                                                                constants.RENDER_ENGINE.re_tex_ext,
                                                                num_error,
                                                                error_dict)
        raise_dialog(message, "Process Finished")

        self.tw_update_retex()
        self.tw_update_all_icons()
        return

    def search_n_replace(self):
        txt_search = self.le_sr_l.text()
        txt_replace = self.le_sr_r.text()
        ignore_expression_status = self.chkbox_sr_expr.isChecked()

        logging.info("--------------- \n"
                     " SearchnReplace for '{}' to '{}' with ignore_expression={}".format(txt_search,
                                                                                         txt_replace,
                                                                                         ignore_expression_status))
        if not txt_search:
            return

        all_qitems_list = self.tw_return_root_items()
        for qitem in all_qitems_list:
            qitem_filepath = qitem.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
            if qitem_filepath in LOCKED_LIST:
                continue

            # use the re module to see if the submitted search text return a match
            match_grp = re.search(txt_search, qitem_filepath)
            if match_grp:
                try:
                    self.qitem_change_path(qitem=qitem, matched_grp=match_grp, replace_txt=txt_replace,
                                           ignore_expression=ignore_expression_status)
                except Exception as excp:
                    logger.error(excp)
            else:
                continue  # the path on this qitem didn't match

        self.populate_treewidget()
        return

    def qitem_change_path(self, qitem, matched_grp, replace_txt, ignore_expression=True):
        """

        Args:
            qitem(QtWidgets.QTreeWidgetItem):
            matched_grp(class '_sre.SRE_Match'):
            replace_txt(str):
            ignore_expression(bool):

        Returns:
            None
        Raises:
            CustomWarning: If the value can't be set on the path parameter
        """

        qitem_path_param = qitem.data(TREEW_DATA["path_parameter"]["column"], QtCore.Qt.UserRole)
        if not qitem_path_param:
            raise DisplayError("Qitem {} doesn't have a path_parameter".format(qitem), "Qt Error")

        filepath_value = os.path.normpath(qitem_path_param.getValue(0))
        if not filepath_value:
            logging.warning("Node {} has an empty filepath".format(qitem_path_param.getNode()))
            return

        if qitem_path_param.isExpression():
            if ignore_expression:
                return
            else:
                qitem_path_param.setExpressionFlag(False)

        filepath_new_value = str(filepath_value.replace(matched_grp.group(), replace_txt))
        try:
            qitem_path_param.setValue(filepath_new_value, 0)
        except Exception as excp:
            raise CustomWarning("Can't change value on path param {} : {}".format(qitem_path_param, excp))

        logging.info(" Changed path for node ({})(match={})(replace={}) \n"
                     " from {}\n"
                     " to {} \n".format(qitem_path_param.getNode(),
                                        matched_grp.group(),
                                        replace_txt,
                                        filepath_value,
                                        filepath_new_value))
        return

    """ --------------
    BAKING RETEX - """

    def bake_selection2retex(self, qitems_selected, all_qitems=False):
        """
        Render Engine agnostic

        Args:
            all_qitems(bool): True to ignore arg qitems_selected and bake all the item in the treewidget
            qitems_selected(list): list of QtWidgets.QTreeWidgetItems

        Returns:
            none
        """
        if not constants.RENDER_ENGINE.support_re_baking:
            _message = "The current render engine {} doesn't support r.e-texture baking".format(
                constants.RENDER_ENGINE.name)
            raise DisplayError(_message, "ReTex baking not supported")

        files2bake = []
        # get all the root items in the treewidget
        if all_qitems:
            qitems_selected = self.tw_return_root_items()

        for qitem in qitems_selected:
            qitem_filepath = self.qitem_return_filepaths(qitem=qitem)
            if qitem_filepath not in LOCKED_LIST:
                files2bake += qitem_filepath

        self._prg_dialog = self._retex_progress_dialog(dialog_length=len(files2bake))

        self.thread = QtCore.QThread(self)
        self.worker = constants.render_engine.common.ReTexBake(file_paths=files2bake,
                                                               render_engine=constants.RENDER_ENGINE)
        self.worker.moveToThread(self.thread)
        self.worker.file_processed.connect(self._retex_processed)
        self.worker.finished.connect(self._retex_finished)

        self._prg_dialog.canceled.connect(self._retex_aborted)
        self.thread.started.connect(self.worker.bake)
        self._prg_dialog.show()
        self.thread.start()

        logger.debug("[retex bake]: Thread started for {}: {}".format(constants.RENDER_ENGINE.name, files2bake))
        self._retex_processed()

    def _retex_processed(self, file_processed=None):
        logger.debug("One file processed: {}".format(file_processed))
        self._prg_dialog.setValue(self._prg_dialog.value() + 1)
        return

    def _retex_aborted(self):
        logger.debug("retex baking aborted by user")
        self.worker.abort = True
        self.thread.quit()

    def _retex_finished(self, error_dict, canceled=False):
        """ Called when baking for render engine finished or aborted by user

        Args:
            error_dict(dict):
            canceled(bool): True if the method has been called due to a Cancel from the user

        Returns:
            None
        """
        num_texture_bake = self._prg_dialog.maximum() - len(error_dict)
        logger.info("\n {} baking completed for {} texture: \n"
                    "  -canceled:{} ,"
                    "  -errors:{}".format(constants.RENDER_ENGINE.re_tex_ext, num_texture_bake, canceled, error_dict))
        self.thread.quit()

        self._prg_dialog.setValue(self._prg_dialog.maximum())  # end the progress dialog

        self.tw_update_retex()
        self.tw_update_all_icons()

        if canceled:
            raise_dialog("Baking canceled by user, some items might have been baked thought.", "Baking Canceled")
        else:
            message = "{} baking completed for {}/{} textures: \n".format(constants.RENDER_ENGINE.re_tex_ext,
                                                                          num_texture_bake,
                                                                          self._prg_dialog.maximum())
            message += "  {} errors: {}".format(len(error_dict), error_dict)
            raise_dialog(message, "Baking finished")
        return

    def _retex_progress_dialog(self, dialog_length):
        prg_dialog = QtWidgets.QProgressDialog("Baking {} Rstex ...".format(dialog_length),
                                               "Abort Operation",
                                               0,
                                               dialog_length,
                                               self)

        prg_dialog.setMinimumDuration(1000)
        return prg_dialog

    """ - END BAKING """

    def populate_treewidget(self):
        """ Populate the tree widget with all the texture in the scene

        Returns:
            bool: False if no items added

        """
        # Clear the treewidget before populating it
        self.tw_remove_items(all_items=True)

        try:
            texture_nodes_dict = constants.RENDER_ENGINE.get_re_texture_nodes()
        except ValueError as excp:
            logger.warning("TreeWidget not updated: {}".format(excp))
            return False

        for node, data in texture_nodes_dict.items():
            file_path = data[0]
            file_param = data[1]
            self.tw_add_item(in_filepath=file_path, ktn_node=node, file_param=file_param)

        self.treewidget.collapseAll()
        self.tw_detect_expression()
        if ENABLE_RETEX:
            self.tw_update_retex()
            self.tw_update_all_icons()
        self.tw_update_path_notexists()
        return True

    def tw_add_item(self, in_filepath, ktn_node, file_param):
        """ Method used to add a new root item to the treewidget

        Args:
            in_filepath(str):
            ktn_node(Nodes3DAPI.ShadingNodeBase):
            file_param:

        Returns:
            QWidgets.QTreeWidgetItem

        """

        new_root_item = TreewidgetItemHandler(self.treewidget,
                                              file_path=in_filepath,
                                              ktn_node=ktn_node,
                                              file_param=file_param).root_item

        return new_root_item

    def tw_remove_items(self, items2remove=None, all_items=False):
        """ Remove a given item or all the items in the TreeWidget

        Args:
            items2remove: List of QTreeWidgetItem or QTreeWidgetItem to remove
            all_items(bool): True to remove all items in the treewidget

        Returns:
            bool: True if sucess

        """
        if all_items:
            self.treewidget.clear()
            return True

        # Ensure items2remove is iterable
        try:
            iter(items2remove)
        except TypeError:
            items2remove = [items2remove]

        for tree_items in items2remove:
            self.treewidget.takeTopLevelItem(self.treewidget.indexOfTopLevelItem(tree_items))

        return True

    def tw_return_root_items(self):
        """ Return all items in the treewidget that are direct child of the invisibleRootItem

        Returns:
            (list of QtWidgets.QTreeWidgetItem): list of QtWidgets.QTreeWidgetItem
        """

        tw_item_list = []

        # source: https://stackoverflow.com/questions/8961449/pyqt-qtreewidget-iterating
        root = self.treewidget.invisibleRootItem()
        child_count = root.childCount()
        # iterate through the direct child of the invisible_root_item
        for index in range(child_count):
            qitem_root = root.child(index)
            tw_item_list.append(qitem_root)

        return tw_item_list

    def tw_detect_expression(self):
        """ Iterate trough the item in the tw and determine if the node source file path is computed from an expression

        Returns:
            None

        """
        qitem_root_list = self.tw_return_root_items()
        for qitem in qitem_root_list:
            # skip if the item is disabled
            if qitem.isDisabled():
                continue
            param = qitem.data(TREEW_DATA["path_parameter"]["column"], QtCore.Qt.UserRole)
            if param.isExpression():
                qitem.setForeground(TREEW_DATA["display_path"]["column"],
                                    QtGui.QBrush(QtGui.QColor(Colors.blue_color[0],
                                                              Colors.blue_color[1],
                                                              Colors.blue_color[2])))
            else:
                qitem.setForeground(TREEW_DATA["display_path"]["column"],
                                    QtGui.QBrush(QtGui.QColor(Colors.text_basic[0],
                                                              Colors.text_basic[1],
                                                              Colors.text_basic[2])))

        return

    def tw_update_path_notexists(self):
        """ Iterate trough the item in the treewidget. IF the item doesn't have child check if its path exists, if not
        the displayed path take a red color.

        Returns:
            None
        """
        qitem_root_list = self.tw_return_root_items()
        for qitem_root in qitem_root_list:
            sub_item_count = qitem_root.childCount()
            # check if the item has child
            if not sub_item_count:
                filepath = qitem_root.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
                if not os.path.exists(filepath):
                    qitem_root.setForeground(TREEW_DATA["display_path"]["column"],
                                             QtGui.QBrush(QtGui.QColor(Colors.red_color[0],
                                                                       Colors.red_color[1],
                                                                       Colors.red_color[2])))  # set root item to red
        return

    def tw_update_retex(self):
        """ Update the renderengine-tex value for all the items in the TreeWidget
        Render Engine agnostic

        Returns:
            None
        """

        qitem_root_list = self.tw_return_root_items()

        for qitem_root in qitem_root_list:
            sub_item_count = qitem_root.childCount()
            if sub_item_count:
                # process childrens
                sub_item_baked_list = []
                for subitem_index in range(sub_item_count):
                    qitem_sub = qitem_root.child(subitem_index)
                    sub_filepath = qitem_sub.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)

                    rstex_baked = constants.render_engine.common.is_retex_baked(sub_filepath,
                                                                      render_engine=constants.RENDER_ENGINE)
                    if rstex_baked:
                        qitem_sub.setData(TREEW_DATA["enginetex_baked"]["column"],
                                          QtCore.Qt.UserRole,
                                          DataRole.all_enginetex)
                    else:
                        qitem_sub.setData(TREEW_DATA["enginetex_baked"]["column"],
                                          QtCore.Qt.UserRole,
                                          DataRole.no_enginetex)
                    sub_item_baked_list.append(rstex_baked)

                # once children are processed, do the root
                if all(sub_item_baked_list):
                    qitem_root.setData(TREEW_DATA["enginetex_baked"]["column"],
                                       QtCore.Qt.UserRole,
                                       DataRole.all_enginetex)
                elif any(sub_item_baked_list):
                    qitem_root.setData(TREEW_DATA["enginetex_baked"]["column"],
                                       QtCore.Qt.UserRole,
                                       DataRole.some_enginetex)
                else:
                    qitem_root.setData(TREEW_DATA["enginetex_baked"]["column"],
                                       QtCore.Qt.UserRole,
                                       DataRole.no_enginetex)

            # else means this is a toplevel item without children:
            else:
                filepath = qitem_root.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
                rstex_baked = constants.render_engine.common.is_retex_baked(filepath,
                                                                            render_engine=constants.RENDER_ENGINE)
                if rstex_baked:
                    qitem_root.setData(TREEW_DATA["enginetex_baked"]["column"],
                                       QtCore.Qt.UserRole,
                                       DataRole.all_enginetex)
                else:
                    qitem_root.setData(TREEW_DATA["enginetex_baked"]["column"],
                                       QtCore.Qt.UserRole,
                                       DataRole.no_enginetex)
            # end of iterating through root items
        return

    def tw_update_all_icons(self):
        """ Iterate trough all the item in th TreeWidget and update their icons

        Returns:
            None
        """
        qitem_root_list = self.tw_return_root_items()
        for qitem_root in qitem_root_list:
            self._tw_update_item_icon(qitem_root)

            sub_item_count = qitem_root.childCount()
            for subitem_index in range(sub_item_count):
                qitem_sub = qitem_root.child(subitem_index)
                self._tw_update_item_icon(qitem_sub)

        return

    def _tw_update_item_icon(self, qitem):
        """ Update the icon on a single qitem

        Args:
            qitem (QtWidgets.QTreeWidgetItem):

        Returns:
            None
        """

        icon_path = get_icon_for_qitem(qitem=qitem)
        pixmap = QtGui.QPixmap(icon_path).scaled(self.size_tw_icons[0],
                                                 self.size_tw_icons[1],
                                                 transformMode=QtCore.Qt.SmoothTransformation)
        qitem.setIcon(0, QtGui.QIcon(pixmap))
        return


class TreewidgetItemHandler:
    root_item_font_size = 7.5
    child_item_font_size = 7

    def __init__(self, treewidget, file_path, ktn_node, file_param, **kwargs):
        """ Create a QTreeWidgetItem with its potential child

        Args:
            file_param (param): # TODO
            treewidget:
            file_path(str):
            ktn_node(Nodes3DAPI.ShadingNodeBase):
            **kwargs: optionnal keyword argument added into TREEW_DATA

        Note:
            If file path is computed from an expression: root item get a blue color
            If child item doesn't exists: red color
        """
        self.treewidget = treewidget
        self.file_path = os.path.normpath(file_path)

        self.locked_item = False
        if file_path in LOCKED_LIST:
            self.locked_item = True  # the created root item is going to be locked

        self.ktn_node = ktn_node
        self.file_param = file_param
        self.kwargs = kwargs

        self.setup()

    def setup(self):

        # return QtWidgets.QTreeWidgetItem
        self.root_item = tw_create_and_add_item(self.treewidget,
                                                font_family=FONT_JetBrainNL_Medium,
                                                font_size=self.root_item_font_size,
                                                locked_item=self.locked_item,
                                                display_path=self.file_path,
                                                katana_node=self.ktn_node,
                                                file_path=self.file_path,
                                                path_parameter=self.file_param,
                                                enginetex_baked=False,
                                                **self.kwargs)

        logger.debug("[TreeWidget] Root-item created for {} with args: {}".format(self.file_path,
                                                                                  [self.file_path, self.ktn_node]))

        child_list = return_children_textures(self.file_path)
        if child_list:
            self._create_child_from_root(root_item=self.root_item, matched_path_list=child_list)
        else:
            # means there is no TOKEN/Pattern use in the file path or the child creation tell the pattern used didn't -.
            # .- return existing files.
            if not os.path.exists(self.file_path):
                # If the file doesn't exists it means there is an error in the path
                self.root_item.setForeground(TREEW_DATA["display_path"]["column"],
                                             QtGui.QBrush(QtGui.QColor(Colors.red_color[0],
                                                                       Colors.red_color[1],
                                                                       Colors.red_color[2])))  # set root item to red
                logging.info(" File path ({}) does not exists".format(self.file_path))
            else:
                # the file exists but doesn't has children so as the root item as already been created return
                pass
        return

    def _create_child_from_root(self, root_item, matched_path_list):
        """ Create QTreeWidgetItems parented to an item

        Args:
            matched_path_list (list): list of file paths
            root_item(QtWidgets.QTreeWidgetItem):

        Returns:
            bool: False if no child created

        """
        for matched_path in matched_path_list:
            # only create child fro existing paths
            if os.path.exists(matched_path):
                locked_item = False
                if self.locked_item or matched_path in LOCKED_LIST:
                    locked_item = True

                display_path = matched_path
                try:
                    tw_create_and_add_item(parent=root_item,
                                           font_color=Colors.child,
                                           font_family=FONT_JetBrainNL_Medium,
                                           font_size=self.child_item_font_size,
                                           locked_item=locked_item,
                                           display_path=display_path,
                                           katana_node=self.ktn_node,
                                           file_path=matched_path,
                                           path_parameter=self.file_param,
                                           enginetex_baked=False,
                                           **self.kwargs)
                except Exception as excp:
                    logger.debug("[Child Item creation]ERROR: {}".format(excp))
                    continue

                logger.debug("  - One child item created: {} ".format(matched_path))
            else:
                logger.debug("[Child Item creation]: path ({}) doesn't exists".format(matched_path))

        return True


def tw_create_and_add_item(parent,
                           font_color=None,
                           font_bold=False,
                           font_family=None,
                           font_size=None,
                           locked_item=False,
                           **kwargs):
    """ Create a QTreeWidgetItem for the given parent
    font* args are used for the display_path (column 0)
    **kwargs keyword should have a name existing as a key in the TREEW_DATA dict

    Args:
        locked_item(bool): if True item.setFlags(QtCore.Qt.NoItemFlags)
        font_size(float):
        font_bold(bool):
        parent (QtWidgets.QTreeWidgetItem or QtWidgets.QTreeWidget)
        font_family (str): font family to use for the display_path
        font_color (tuble): tuple of 3 integers written in 8bit notation ex: (150,255,15), for the display_path
        **kwargs

    Keyword Args:
        file_param (NodegraphAPI.Parameter):
        file_path (str):
        display_path(str): file path
        ktn_node(Nodes3DAPI.ShadingNodeBase): Nodes3DAPI.ShadingNodeBase node (depends of the Render Engine)

    Returns:
        QtWidgets.QTreeWidgetItem

    Raises:
        TreeWidgetItemError: if item cannot be created
    """
    try:
        qitem = QtWidgets.QTreeWidgetItem(parent)
    except Exception as excp:
        raise TreeWidgetItemError("QTWItem cannot be created for parent {} : {}".format(parent, excp))

    for key_arg, arg_value in kwargs.items():
        treew_data_dict = TREEW_DATA.get(key_arg, False)
        if not treew_data_dict:
            logger.debug("[TWItem creation]: kwarg ({}={}) not found in TREEW_DATA".format(key_arg, arg_value))
            continue

        if treew_data_dict["visible"]:
            qitem.setText(treew_data_dict["column"], arg_value)
        else:
            qitem.setData(treew_data_dict["column"], QtCore.Qt.UserRole, arg_value)

    # Modify the column 0
    qitem.setTextAlignment(TREEW_DATA["display_path"]["column"], QtCore.Qt.AlignLeft)

    qfont = qitem.font(TREEW_DATA["display_path"]["column"])
    if font_color:
        qitem.setForeground(TREEW_DATA["display_path"]["column"],
                            QtGui.QBrush(QtGui.QColor(font_color[0], font_color[1], font_color[2])))
    if font_bold:
        qfont.setBold(True)
    if font_family:
        qfont.setFamily(font_family)
    if font_size:
        qfont.setPointSizeF(font_size)

    qitem.setFont(TREEW_DATA["display_path"]["column"], qfont)
    if locked_item:
        qitem.setFlags(QtCore.Qt.NoItemFlags)
        qitem.setForeground(TREEW_DATA["display_path"]["column"],
                            QtGui.QBrush(QtGui.QColor(Colors.text_disable[0],
                                                      Colors.text_disable[1],
                                                      Colors.text_disable[2])))
    return qitem


def get_texture_dict_from_twitem(twitem_list):
    """

    Args:
        twitem_list(list of QtWidgets.QTreeWidgetItem):

    Returns:
        dict: {KatanaNode: [file_path, file_param]}
    """

    all_texture_node = {}
    for qitems_root in twitem_list:
        file_path = qitems_root.data(TREEW_DATA["file_path"]["column"], QtCore.Qt.UserRole)
        if file_path in LOCKED_LIST:
            continue
        ktn_node = qitems_root.data(TREEW_DATA["katana_node"]["column"], QtCore.Qt.UserRole)  # int from DataRole
        file_param = qitems_root.data(TREEW_DATA["path_parameter"]["column"], QtCore.Qt.UserRole)
        # construct the dict for the KLF baking
        all_texture_node[ktn_node] = [file_path, file_param]

    return all_texture_node


def get_textures_path_from_texturenodesdict(texturenodes_dict):
    """ Iterate trough a dictionnary of file_path and return the potential children

    Args:
        texturenodes_dict(dict): {KatanaNode: [file_path, file_param]}

    Returns:
        list
    """
    textures_path_list = []
    for ktn_node, data in texturenodes_dict.items():
        file_path = data[0]
        children_list = return_children_textures(file_path)
        if children_list:
            textures_path_list += children_list
        else:
            textures_path_list.append(file_path)

    logger.debug(textures_path_list)
    return textures_path_list


