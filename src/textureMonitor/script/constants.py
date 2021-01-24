"""
Author: Liam Collod
Last Modified: 16/01/2020

Any Python Version
Katana script:
    tested on 3.6v4
"""
import os
import json
import logging

from UI4.App import MainWindow

from . import render_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

VERSION = "1.0.0"
APPNAME = "Texture Monitor"

KATANA_MAIN_WIND = MainWindow.GetMainWindow()  # UI4.App.MainWindow.KatanaWindow
INSTALL_PATH = os.path.dirname(__file__)  # return a folder path
RESOURCES_LOCATION = os.path.normpath(os.path.join(INSTALL_PATH, '..', 'resources'))

""" ---------------------
User settings loading """

user_settings = {}
_settingspath = os.path.normpath(os.path.join(INSTALL_PATH, '..', 'settings.json'))
if os.path.exists(_settingspath):
    with open(_settingspath, "r") as jsonfile:
        user_settings = json.load(jsonfile)
        logger.debug("[JSON]: User settings: {}".format(user_settings))

else:
    logger.warning("Json settings file ({}) doesn't exists".format(_settingspath))

# determine which render engine to use in the script, this must be a module located in ./render_engine
RENDER_ENGINE = eval("render_engine.{}".format(user_settings.get("default_render_engine"), "Delight"))
# List of filepaths that when used in an Item will make it lock to the user (qitem.setFlags(QtCore.Qt.NoItemFlags))
LOCKED_LIST = user_settings.get("locked_paths", [])
# this will enable/disable the render-egine texture specific features including icons.
ENABLE_RETEX = user_settings.get("enable_retex", True)
# interface width in pixels
UI_WIDTH = user_settings.get("default_ui_width", 1200)

# not an user setting
RENDER_ENGINES_AVAILABLE = render_engine.render_engines  # list of str


""" TREEWIDGET -------------------------------------------------------------------------------------------------------
This variable determined which column of the tree widget hold which property 
{
key_name(str): {
    column (str): (int),
    display_pretty_name (str): (str),
    is_visible (str): (bool)
    }
}
"""

TREEW_DATA = {
    "display_path": {"column": 0,  # This is locked, do not touch
                     "pretty_name": "File Path",
                     "visible": True},

    "katana_node": {"column": 1,
                    "pretty_name": "Katana Node",
                    "visible": False},

    "file_path": {"column": 2,
                  "pretty_name": "File Path",
                  "visible": False},

    "path_parameter": {"column": 3,
                       "pretty_name": "Path Parameter",
                       "visible": False},

    "enginetex_baked": {"column": 4,
                        "pretty_name": "Engine Tex",
                        "visible": False},

}


class DataRole:
    """
    Variable used to hold information through the QtTreeWidgetItems
    """
    all_enginetex = 1
    no_enginetex = 0
    some_enginetex = 2


