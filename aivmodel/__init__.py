import ctypes
import ctypes.wintypes
# import cyminhook
import win32api
import win32con
import traceback

from lua import registerCallback

global process

# ptrCurrentUnitID = ctypes.POINTER(ctypes.c_int32)(ctypes.c_long(0x00ee0fc8))

handlers = []

callbackType = ctypes.WINFUNCTYPE(ctypes.c_int32, ctypes.c_int32)

@callbackType
def onLordKilled(playerID):
  # TODO: also receive how many players there are in the game I guess... Nice to have dynamically
  # The reason is that one wants to distinguish wins by the AI from losses.
  try:
    if len(handlers) > 0:
      if handlers[0].initialized == False:
        try:
          handlers[0].initialize()
        except Exception as e:
          win32api.MessageBox(None, f"{e}", "Error during handler initialization", win32con.MB_OK)
          return False
      return 1 if handlers[0].onLordKilled(playerID) == True else 0
    
    answer = win32api.MessageBox(None, f"Player #{playerID} died.\nRestart the game?", "A lord died!", win32con.MB_OKCANCEL)
    return 1 if answer == 1 else 0
  except Exception as e:
    win32api.MessageBox(None, f"{''.join(traceback.TracebackException.from_exception(e).format())}", "Error during onLordKilled", win32con.MB_OK)
    return False


def set_handler(handler):
  handlers.clear()
  handlers.append(handler)

try:
  registerCallback("onLordKilled", onLordKilled, 1)
except Exception as e:
  win32api.MessageBox(None, f"{e}", "Error during handler initialization", win32con.MB_OK)