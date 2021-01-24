"""
Custom Exceptions

Author: Liam Collod
Last Modified: 10/01/2020

All Python versions
"""

from PyQt5 import QtWidgets

from . import constants


class BaseError(Exception):
    """
    Base class for all errors
    """
    pass


class DisplayError(BaseError):
    def __init__(self, message, exception_type):
        """ Raise the error and display it to the user trough a small dialog

        Args:
            message(str):
            exception_type(str): something like "ERROR" or "WARNING"
        """
        self.message = message
        self.exception_type = exception_type

    def __str__(self):
        error_message = "\n"
        error_message += '---[{}]--------- \n'.format(self.exception_type)
        error_message += "  > {} \n".format(self.message)

        raise_dialog(error_message, self.exception_type)  # raise a window for the user
        return error_message


class CustomWarning(BaseError):
    def __init__(self, message):
        super(CustomWarning, self).__init__(message)


class KatanaAPIerror(BaseError):
    pass


class TreeWidgetItemError(BaseError):
    pass


def raise_dialog(message, title):
    """ Raise a dialog window that display a single message

    Args:
        message(str): message to write
        title(str): title of the window


    """
    dialog = QtWidgets.QDialog(parent=constants.KATANA_MAIN_WIND)
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

