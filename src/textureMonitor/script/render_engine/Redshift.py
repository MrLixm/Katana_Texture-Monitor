"""
Redshift Render engine

Author: Liam Collod
Last Modified: 16/01/2020

Python 2.7 only
Katana script, tested on 3.6v4
"""

import logging
import os
import subprocess

from Katana import NodegraphAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

name = "Redshift"
re_tex_ext = ".rstexbin"
support_re_baking = True


""" 
Could be also called token, they are used in file path to load multiple files in one path
    - the dict key is a regular expression
    - the dict value is a glob module expression """

PATH_PATTERN = {
    '<UDIM>': "[1][0-2][0-9][0-9]",
    '<UVTILE>': "?*_*[0-9]"
}


def _find_retexture_processor():
    """ Redshift specific

    Returns:
        str: path to the redshiftTextureProcessor.exe
    """
    local_path = "C:\\Redshift\\bin\\redshiftTextureProcessor.exe"
    if os.path.exists(local_path):
        return local_path

    local_path02 = "C:\\ProgramData\\Redshift\\bin\\redshiftTextureProcessor.exe"
    if os.path.exists(local_path02):
        return local_path02

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
            rstex_path if success else False if error
    Raises:
        ValueError: if file_path arg is not a string

    """
    if not isinstance(file_path, basestring):  # TODO python2 specific
        raise ValueError("filepath submitted is not a string but {}: {}".format(type(file_path), file_path))

    command = "{} {} -l ".format(re_textool, file_path)
    result = subprocess.check_output(command)
    logger.debug("rstexprocessor result: {}".format(result))

    # check success of baking
    source_path, filename = os.path.split(file_path)
    basename, extension = os.path.splitext(filename)
    rstex_path = os.path.join(source_path, "{}.rstexbin".format(basename))
    if not os.path.exists(rstex_path):
        return False

    return rstex_path


def get_re_texture_nodes():
    """ Get all Redshift TextureSampler Nodes

    Returns:
        dict: Dictionnary of KatanaNode:[file_path value, file_path_parameter]

    """

    texture_sampler_dict = {}  # init the dict

    all_node_list = NodegraphAPI.GetAllNodesByType('RedshiftShadingNode', includeDeleted=False, sortByName=True)
    for ktnnode in all_node_list:
        # check if you can get the type of the node
        try:
            node_type_value = ktnnode.getParameter("nodeType").getValue(0)
        except:
            continue

        if node_type_value == "TextureSampler":
            # try to get the file_path in the TextureSampler
            ts_path_param = ktnnode.getParameter('parameters.tex0.value')
            try:
                file_path = str(ts_path_param.getValue(0))
            except Exception as excp:
                logger.warning("Cannot get the filepath for node {}: {}".format(ktnnode, excp))
                continue  # skip to the next item

            if file_path:
                texture_sampler_dict[ktnnode] = [os.path.normpath(file_path), ts_path_param]

    if texture_sampler_dict:
        return texture_sampler_dict
    else:
        raise ValueError("No textures find in scene")


def return_retex_from_path(file_path):
    """ Return the path of the render engine texture corresponding to the given file paths

    Args:
        file_path(stre or basestring):

    Returns:
        str: file path corresponding to the render engine texture type, the file path may not exists
    """
    if not isinstance(file_path, basestring):  # TODO python2 specific
        raise ValueError("filepath submitted is not a string but {}: {}".format(type(file_path), file_path))

    source_path, filename = os.path.split(file_path)
    basename, _extension = os.path.splitext(filename)
    retex_path = os.path.join(source_path, "{}{}".format(basename, re_tex_ext))

    return retex_path
