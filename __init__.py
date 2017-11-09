from .channel_logger import DataLogger

# enable ipython QtGui support if needed
try:
    from IPython import get_ipython
    IPYTHON = get_ipython()
    IPYTHON.magic("gui qt")
except BaseException as e:
    logger.debug('Could not enable IPython gui support: %s.' % e)

# get QApplication instance
from qtpy import QtCore, QtWidgets
APP = QtWidgets.QApplication.instance()
if APP is None:
    APP = QtWidgets.QApplication(['pyrpl'])