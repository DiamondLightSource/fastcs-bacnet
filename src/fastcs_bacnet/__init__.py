"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by https://github.com/pypa/setuptools_scm
"""

import pathlib
import sys

from ._version import __version__

file_path = pathlib.Path(__file__)

dls_bms_path = file_path.parent.parent / "dls_bms"

sys.path.append(str(dls_bms_path))

__all__ = ["__version__"]
