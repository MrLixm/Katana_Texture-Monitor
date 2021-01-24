"""
This file hold RENDER ENGINE AGNOSTIC FUNCTIONS

Author: Liam Collod
Last Modified: 03/01/2020

Python 2 specific (see TODO)
Katana script:
    tested on 3.6v4
"""

import os

from PyQt5 import QtCore


def is_retex_baked(file_path, render_engine):
    """ Return true if the render engine texture corresponding to the given file exists
    Render engine agnostic

    Args:
        render_engine (module):module Representing a RenderEngine
        file_path(str):

    Returns:
        bool: True if the rstex corresponding to the given file exists

    """
    if not os.path.exists(file_path):
        return False  # TODO see to raise error

    retex_path = render_engine.return_retex_from_path(file_path=file_path)
    return os.path.exists(retex_path)


# To use in a QThread
class ReTexBake(QtCore.QObject):
    file_processed = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(list, bool)

    def __init__(self, file_paths, render_engine):
        """ RenderEngine agnostic

        Args:
            render_engine (class): class item Representing a RenderEngine
            file_paths(list or tuple):  iterable of file path to bake to an rstex
        """
        super(ReTexBake, self).__init__()
        self.file_paths = file_paths
        self.error_list = []
        self.abort = False
        self.render_engine = render_engine

    def bake(self):
        """

        Emit:
        finished(list): list of file path that didn't get converted if any
        """
        for file2bake in self.file_paths:
            if self.abort:
                break  # stop the loop and emit finished
            bake_result = self.render_engine.bake_retex(file2bake)  # bool
            if not bake_result:
                self.error_list.append(bake_result)
            self.file_processed.emit(file2bake)

        self.finished.emit(self.error_list, self.abort)
