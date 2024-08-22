import ctypes

# luabuiltins is set by the module
from luabuiltins import LUA_REGISTER_CALLBACK_ADDRESS

def pointerOfFunction(func):
  return ctypes.c_ulong.from_address(ctypes.addressof(func)).value

registerCallbackType = ctypes.WINFUNCTYPE(ctypes.c_int32, ctypes.c_char_p, ctypes.c_int32, ctypes.c_int32)
_LUA_REGISTER_CALLBACK = registerCallbackType(LUA_REGISTER_CALLBACK_ADDRESS)
def registerCallback(name, func, argCount = None):
  if argCount == None:
    argCount = len(func.argtypes)
  if _LUA_REGISTER_CALLBACK != None:
    _LUA_REGISTER_CALLBACK(name.encode('ascii'), pointerOfFunction(func), argCount)