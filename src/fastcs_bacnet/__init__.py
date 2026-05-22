"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by https://github.com/pypa/setuptools_scm
"""

import os
import sys

from ._version import __version__

file_path = os.path.realpath(__file__)

path_to_src = file_path.replace("fastcs_bacnet/__init__.py", "")
print(path_to_src + "dls_bms")

sys.path.append(path_to_src + "dls_bms")

__all__ = ["__version__"]
