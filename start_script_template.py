"""
Place all your intilialization routines here.

Functions or coroutines defined in this file can be called by each channels to
perform a measurement.

To try them out, set the "callback" field of a channel to either "random_func"
or "random_coroutine"

The script can be re-run to take into account the lattest modifications by
right-clicking in the channel tree view.
"""

## option 1. use a standard function returning a float
def random_func():
    import numpy as np # don't know why it needs to be imported here
    return np.random.rand()

## option 2. use a coroutine to perform the measurement asynchronously
## (This is the case of all functions based on SerialInterface.ask)
async def random_coroutine():
    import asyncio
    import numpy as np
    await asyncio.sleep(0.1)
    return np.random.rand()