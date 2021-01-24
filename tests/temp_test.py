"""
pass
"""

import glob
import os

PATH_PATTERN = {'<UDIM>': "[1][0-2][0-9][0-9]",
                '<UVTILE>': "?*_*[0-9]"}


main_path = r"J:\STIM_STUDIO\Projects\2009_witches\01_ROOT\ASSETS\SET\placeGround\PROJECT\sourceimages\placeGround_textures\01-WorkinfFiles\export_mari_v01_4k\placeGround_Diffuse_Color_<UDIM>.exr"

tag2match = '<UDIM>'
match_path = main_path.replace(tag2match, PATH_PATTERN.get(tag2match))
for file_path in glob.glob(match_path):
    print(os.path.exists(file_path), file_path)

##########################

from PyQt5 import QtWidgets, QtCore, QtGui
from UI4.App import MainWindow

KATANA_MAIN_WIND = MainWindow.GetMainWindow()  # UI4.App.MainWindow.KatanaWindow


class BaseError(Exception):
    def __init__(self, message, exception_type, raise_message_dialog=False):
        """

        Args:
            raise_message_dialog (bool): True to display the exception to the user with a small dialog
            message(str):
            exception_type(str): something like "ERROR" or "WARNING"
        """
        self.raise_dialog = raise_message_dialog
        self.message = message
        self.exception_type = exception_type

    def __str__(self):
        error_message = "\n"
        error_message += '---[{}]--------- \n'.format(self.exception_type)
        error_message += "  > {}".format(self.message)

        if self.raise_dialog:
            raise_dialog(error_message, self.exception_type)  # raise a window for the user
        return error_message


class CustomError(BaseError):
    def __init__(self, message):
        super(CustomError, self).__init__(message=message, exception_type="ERROR", raise_message_dialog=True)


class CustomWarning(BaseError):
    def __init__(self, message):
        super(CustomWarning, self).__init__(message=message, exception_type="WARNING", raise_message_dialog=False)


def raise_dialog(message, title):
    """ Raise a dialog window that display a single message

    Args:
        message(str): message to write
        title(str): title of the window


    """
    dialog = QtWidgets.QDialog(parent=KATANA_MAIN_WIND)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(350)
    dialog.setMinimumHeight(150)

    button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
    button_box.accepted.connect(dialog.accept)

    lbl_dialog = QtWidgets.QLabel(message)

    lyt_dialog = QtWidgets.QVBoxLayout()
    lyt_dialog.addWidget(lbl_dialog)
    lyt_dialog.addWidget(button_box)

    dialog.setLayout(lyt_dialog)

    dialog.exec_()
    return


def test():
    raise CustomError("Something happens i don't know")

test()