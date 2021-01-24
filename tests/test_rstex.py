import glob
import os
import subprocess

def return_retex_from_path(file_path):
    """ Return the path of the render engine texture corresponding to the given file paths

    Args:
        file_path(stre or basestring):

    Returns:
        str: file path corresponding to the render engine texture type
    """
    if not isinstance(file_path, str):  # TODO python2 specific
        raise ValueError("filepath submitted is not a string but {}: {}".format(type(file_path), file_path))

    source_path, filename = os.path.split(file_path)
    basename, _extension = os.path.splitext(filename)
    retex_path = glob.glob(os.path.join(source_path, "{}*{}".format(basename, ".tdl")))
    if not retex_path:
        return ""
    return retex_path[0]

path_v = r"L:\PROJECT_personal\A2_bb8\PROJECT\sourceimages\bb8_textures\FINAL\bb8_aceschg_Anistropy_1012.exr"
result = return_retex_from_path(path_v)
print(result)
print(os.path.exists(result))
