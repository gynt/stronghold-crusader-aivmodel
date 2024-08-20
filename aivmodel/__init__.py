import ctypes
import ctypes.wintypes
# import cyminhook
import win32api
import win32con

from pymem import Pymem

global process

ptrCurrentUnitID = ctypes.POINTER(ctypes.c_int32)(ctypes.c_long(0x00ee0fc8))

callbackType = ctypes.WINFUNCTYPE(ctypes.c_int32, ctypes.c_int32)

@callbackType
def onLordKilled(playerID):
  # TODO: also receive how many players there are in the game I guess... Nice to have dynamically
  # The reason is that one wants to distinguish wins by the AI from losses.
  answer = win32api.MessageBox(None, f"Player #{playerID} died.\nRestart the game?", "A lord died!", win32con.MB_OKCANCEL)
  return True if answer == 1 else 0

import time

def registerCallback(pid):
  global process
  process = Pymem(pid)
  process.write_ulong(0x004865fb, ctypes.c_ulong.from_address(ctypes.addressof(onLordKilled)).value)


def main(pid):
  registerCallback(pid)

  # As this code is in another thread, 
  # we sleep here to avoid garbage collecting the callback.
  # Perhaps some useful computation could be done here
  # while waiting for the game to finish?
  while True:
    time.sleep(1)