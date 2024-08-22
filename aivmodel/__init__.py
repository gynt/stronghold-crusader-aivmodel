import ctypes
import ctypes.wintypes
# import cyminhook
import win32api
import win32con
import time

from pymem import Pymem

global process

# ptrCurrentUnitID = ctypes.POINTER(ctypes.c_int32)(ctypes.c_long(0x00ee0fc8))

handlers = []

callbackType = ctypes.WINFUNCTYPE(ctypes.c_int32, ctypes.c_int32)

@callbackType
def onLordKilled(playerID):
  # TODO: also receive how many players there are in the game I guess... Nice to have dynamically
  # The reason is that one wants to distinguish wins by the AI from losses.
  if len(handlers) > 0:
    if handlers[0].initialized == False:
      try:
        handlers[0].initialize()
      except Exception as e:
        win32api.MessageBox(None, f"{e}", "Error during handler initialization", win32con.MB_OK)
        return False
    return handlers[0].onLordKilled(playerID)
  
  answer = win32api.MessageBox(None, f"Player #{playerID} died.\nRestart the game?", "A lord died!", win32con.MB_OKCANCEL)
  return True if answer == 1 else 0


def _registerCallback(pid):
  global process
  process = Pymem(pid)
  process.write_ulong(0x004865fb, ctypes.c_ulong.from_address(ctypes.addressof(onLordKilled)).value)

def set_handler(handler):
  handlers.clear()
  handlers.append(handler)


def main(pid, handler = None):
  try:
    _registerCallback(pid)

    if handler:
      set_handler(handler)

    # As this code was called from another thread that the game's code, 
    # we sleep here to avoid garbage collecting everything defined, such as the callback.
    # Perhaps some useful computation could be done here
    # while waiting for the game to finish?
    while True:
      time.sleep(1)
  except Exception as e:
    win32api.MessageBox(None, f"{e}", "Error during handler initialization", win32con.MB_OK)