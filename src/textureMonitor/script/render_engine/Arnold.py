"""
Arnold Render engine

Author: Liam Collod
Last Modified: 16/01/2020

Python 2.7 only
Katana script, tested on 3.6v4
"""
import os
import glob
import logging

from Katana import NodegraphAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

name = "Arnold"
re_tex_ext = ".tx"
support_re_baking = False  # set to true to allow to bake the render engine texture

""" 
Could be also called token, they are used in file path to load multiple files in one path
    - the dict key is a regular expression
    - the dict value is a glob module expression 
    As Arnold allow to use token evaluated at rendertime, returning the exact path its refer to is impossible and thus
    only potential children are going to be returned
    """

PATH_PATTERN = {
    '<udim>': "[1][0-2][0-9][0-9]",
    '<UDIM>': "[1][0-2][0-9][0-9]",
    '<tile>': "?*_*[0-9]",
    '<.+?>': "*"  # this one will match token like  <attr:myUserData> or and will return **potential** children
}
# For arnold more detail about token here: https://docs.arnoldrenderer.com/display/A5AFMUG/Tokens


def _find_retexture_processor():
    """ Return the path to the render engine texture processor tool

    Returns:
        str: path to the maketx.exe
    """
    local_path = r"C:\Program Files\Autodesk\Arnold\maya*\bin\maketx.exe"
    possible_maketx_path = glob.glob(local_path)
    if possible_maketx_path:
        return possible_maketx_path[-1]

    else:
        if support_re_baking:
            raise RuntimeError("The renderengine texture processor cannot be found for {}".format(name))
        else:
            logger.info("The renderengine texture processor cannot be found for {} but re baking is disabled".format(
                name
            ))


re_textool = _find_retexture_processor()


def bake_retex(file_path):
    """ Bake the render engine texture of the given file_path

    Args:
        file_path(str):  file path to bake

    Returns:
        bool:
            render engine texture path if success else False if error
    Raises:
        ValueError: if file_path arg is not a string

    """
    if not isinstance(file_path, basestring):  # TODO python2 specific
        raise ValueError("filepath submitted is not a string but {}: {}".format(type(file_path), file_path))

    # TODO not supported yet
    return


def get_re_texture_nodes():
    """ Get all Render Engine Katana Texture/File nodes

    Returns:
        dict: Dictionnary of {KatanaNode:[file_path value, file_path_parameter]}
    Raises:
        ValueError
    """
    retex_node_dict = {}

    all_node_list = NodegraphAPI.GetAllNodesByType('ArnoldShadingNode', includeDeleted=False, sortByName=True)
    for ktnnode in all_node_list:
        # check if you can get the type of the node
        try:
            node_type_value = ktnnode.getParameter("nodeType").getValue(0)
        except:
            continue

        if node_type_value == "image":
            # try to get the file_path in the TextureSampler
            ts_path_param = ktnnode.getParameter('parameters.filename')
            try:
                file_path = str(ts_path_param.getValue(0))
            except Exception as excp:
                logger.warning("Cannot get the filepath for node {}: {}".format(ktnnode, excp))
                continue  # skip to the next item

            if file_path:
                retex_node_dict[ktnnode] = [os.path.normpath(file_path), ts_path_param]

    if retex_node_dict:
        return retex_node_dict
    else:
        raise ValueError("No textures find in scene")


def return_retex_from_path(file_path):
    """ Return the path of the render engine texture corresponding to the given file paths

    Args:
        file_path(stre or basestring):

    Returns:
        str: file path corresponding to the render engine texture type or empty string if nt found
    """
    if not isinstance(file_path, basestring):  # TODO python2 specific
        raise ValueError("filepath submitted is not a string but {}: {}".format(type(file_path), file_path))

    source_path, filename = os.path.split(file_path)
    basename, _extension = os.path.splitext(filename)
    retex_path = glob.glob(os.path.join(source_path, "{}*{}".format(basename, ".tx")))
    if not retex_path:
        return ""
    return retex_path[0]
