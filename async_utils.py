import asyncio
from qtpy import QtWidgets

APP = QtWidgets.QApplication.instance()


def wait(coroutine, timeout=None):
    fut = asyncio.ensure_future(coroutine)
    if timeout is not None:
        fut_sleep = asyncio.ensure_future(asyncio.sleep(timeout))
    while not fut.done():
        if timeout:
            if fut_sleep.done():
                break
        APP.processEvents()
    return fut.result()
