"""
Author: Liam Collod
Last Modified: 10/01/2020

All python version
All OS
"""

import os
import glob
import logging
import re
import webbrowser

from . import constants

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def return_children_textures(source_texture):
    """ From a given file path return its potential children. By children, it means other files that are associated
    to the source thanks to a tokken/pattern like <UDIM>.

    Args:
        source_texture(str): filepath

    Returns:
        list of str or bool:
            False if no children found else list of matched children
    """

    source_path, filename = os.path.split(source_texture)  # split the path to apply search only on the filename
    pattern_find_list = []
    for pattern, pattern_match in constants.RENDER_ENGINE.PATH_PATTERN.items():
        c_pattern = re.compile(pattern)
        match_grp = c_pattern.findall(filename)
        if match_grp:  # this means there is more than one texture (ex: UDIM)
            filename = c_pattern.sub(pattern_match, filename)
            pattern_find_list.append(pattern)

    if filename == os.path.split(source_texture)[-1]:
        # means there was no pattern replace in the original source_texture path so no children will be find
        return False
    path2match = os.path.join(source_path, filename)
    matched_path_list = glob.glob(path2match)  # list of file path
    if not matched_path_list:  # means there is an error in the filepath given by the user (no file found)
        return False
    else:
        logger.debug("{} child find for texture {} with token {}".format(len(matched_path_list),
                                                                         source_texture, pattern_find_list))
        return matched_path_list


def open_file_inexplorer(path2open):
    """ Open the given file path in the OS explorer

    Args:
        path2open(str):

    Returns:
        bool: True if sucess
    """
    if not os.path.exists(path2open):
        logger.error(" Can't open path ({}), it doesn't exist".format(path2open))
        return False

    webbrowser.open(path2open)

    return True

