import multiprocessing
import sys


def get_multiprocessing_context():
    """
    Stolen from PythonSoftIOC
    We require a similar testing setup as we are also testing EPICS IOCs

    Original DocString:
    ""
    Tests must use "forkserver" method. If we use "fork" we inherit some
    state from Channel Access from test-to-test, which causes test hangs.

    We cannot use multiprocessing.set_start_method() as it doesn't work inside
    of Pytest.
    ""
    """
    if sys.platform == "win32":
        start_method = "spawn"
    else:
        start_method = "forkserver"
    return multiprocessing.get_context(start_method)
