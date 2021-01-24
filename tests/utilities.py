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



PATH_PATTERN = {
    '<udim>': "[1][0-2][0-9][0-9]",
    '<UDIM>': "[1][0-2][0-9][0-9]",
    '<.+?>': "*"
}  # TODO probably incomplete

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
    for pattern, pattern_match in PATH_PATTERN.items():
        c_pattern = re.compile(pattern)
        match_grp = c_pattern.findall(filename)
        if match_grp:  # this means there is more than one texture (ex: UDIM)
            print(match_grp)
            filename = c_pattern.sub(pattern_match, filename)

    print(filename)
    if filename == os.path.split(source_texture)[-1]:
        # means there was no pattern replace in the original source_texture path
        return False
    path2match = os.path.join(source_path, filename)
    matched_path_list = glob.glob(path2match)  # list of file path
    if not matched_path_list:  # means there is an error in the filepath given by the user (no file found)
        return False
    else:
        logger.debug("{} child find for texture {} with token {}".format(len(matched_path_list),
                                                                         source_texture, pattern))
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


def _find_retexture_processor():
    """ Return the path to the render engine texture processor tool

    Returns:
        str: path to the redshiftTextureProcessor.exe
    """
    local_path = r"C:\Program Files\Autodesk\Arnold\maya*\bin\maketx.exe"
    possible_maketx_path = glob.glob(local_path)
    if possible_maketx_path:
        return possible_maketx_path[-1]

    raise RuntimeError("The renderengine texture processor cannot be found for".format())


if __name__ == '__main__':
    re_textool = _find_retexture_processor()
    print(re_textool)