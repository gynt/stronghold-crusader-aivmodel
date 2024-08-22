
-- registerPythonFunction(name, address)
local registerCallbackLocation = core.allocateCode({0x90, 0x90, 0x90, 0x90, 0x90, 0xC2, 0x0C, 0x00}) -- stdcall three arguments
local originalRegisterCallback -- useless

local pythonCallbacks = {}
local pythonCallbackData = {}
local function registerCallback(name, address, argCount)
  log(VERBOSE, string.format("Registering python callback: %s, %X, %s", name, address, argCount))
  pythonCallbacks[name] = core.exposeCode(address, argCount, 2) -- everything is stdcall, or WINFUNCTYPE
  pythonCallbackData[name] = {address = address, argCount = argCount, name = name}
end
local function rawRegisterCallback(ptrName, address, argCount)
  return registerCallback(core.readString(ptrName), address, argCount)
end

originalRegisterCallback = core.hookCode(rawRegisterCallback, registerCallbackLocation, 3, 2, 5)

local _restart = core.exposeCode(0x00494950, 1, 0)
local restart = function()
  core.writeInteger(0x01126600, 0x2c)
  _restart(0x16)
end

local ptrCurrentUnitID = 0x00ee0fc8

local pythonDLL

local function initializePython(dllPath)
  local dllPath = dllPath
  if dllPath == nil or dllPath:len() == 0 then
    local username = os.getenv("USERNAME")
    dllPath = "C:\\Users\\" .. username .. "\\AppData\\Local\\Programs\\Python\\Python38-32\\python38.dll"
  end

  pythonDLL = ucp.internal.loadLibraryA(dllPath)
  local init = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "Py_Initialize"), 0, 0)
  init()
end

local function executePythonString(s)
  if s == nil or s:len() == 0 then
    log(WARNING, "No python string")
    return
  end

  local runSimpleStringAddr = ucp.internal.getProcAddress(pythonDLL, "PyRun_SimpleString")
  local runSimpleString = core.exposeCode(runSimpleStringAddr, 1, 0)

  return runSimpleString(ucp.internal.registerString(s))
end

local function executePythonFile(filePath)
  local filePath = filePath
  if filePath == nil or filePath:len() == 0 then
    log(WARNING, "No python file set")
    return
  else 
    filePath = ucp.internal.resolveAliasedPath(filePath)
    log(VERBOSE, "executePythonFile: " .. filePath)
  end

  local runSimpleFileAddr = ucp.internal.getProcAddress(pythonDLL, "PyRun_SimpleFile")
  local runSimpleFile = core.exposeCode(runSimpleFileAddr, 2, 0)
  local filePointer, err = io.openFilePointer(filePath, 'rb')
  print(filePointer, err)
  if filePointer == nil then
    error(err)
  end
  local filePathString = ucp.internal.registerString(filePath:match("([^\\/]*[.]py)$") or filePath)

  log(VERBOSE, string.format("runSimpleFile (%s): %s, %s", core.readString(filePathString), filePointer, filePathString))
  return runSimpleFile(filePointer, filePathString)
end


return {
  enable = function(self, config)

    if config.enabled ~= true then return end

    log(VERBOSE, "initialize python: " .. (config.pythonDLLPath or ""))
    log(VERBOSE, initializePython(config.pythonDLLPath))

    --log(VERBOSE, "set _LUA_REGISTER_CALLBACK_ADDRESS")
    --log(VERBOSE, setLuaRegisterCallbackAddress())

    local aivmodelBase = ucp.internal.resolveAliasedPath("ucp/modules/python-interface/")
   -- Monkey patch
    log(VERBOSE, "import aivmodel")
    log(VERBOSE, executePythonString([[
import sys
import win32api, win32con
from types import ModuleType

# import main aivmodel so we can catch any imports here already
try:
  # Insert a place to find modules from
  sys.path.insert(0, "]] .. aivmodelBase .. [[")
  
  _luabuiltins = ModuleType("luabuiltins")
  sys.modules[_luabuiltins.__name__] = _luabuiltins
  _luabuiltins.LUA_REGISTER_CALLBACK_ADDRESS = ]] .. tostring(registerCallbackLocation) .. [[
  
  import luabuiltins
  import lua
  import aivmodel
except Exception as e:
  win32api.MessageBox(None, f"{e}", "Error during aivmodel initialization", win32con.MB_OK)
    ]]))

    -- log(VERBOSE, "read aivmodel callback addresses")
    -- log(VERBOSE, string.format("%X", storeCallbackAddresses()))

    --log(VERBOSE, executePythonFile(config.aivmodel.pythonFilePath))
    if config.pythonFilePath then
      log(VERBOSE, "execute python file: " .. config.pythonFilePath)      
      log(VERBOSE, executePythonString([[
import runpy

try:
  runpy.run_path(']] .. ucp.internal.resolveAliasedPath(config.pythonFilePath) .. [[')
except Exception as e:
  import win32api, win32con
  win32api.MessageBox(None, f"{e}", "Error during aivmodel initialization", win32con.MB_OK)
    ]]))
    end

    core.detourCode(function(registers)
      local unitID = core.readInteger(ptrCurrentUnitID)
      local playerID = core.readSmallInteger(0x013885e2 + (0x490 * unitID))

      log(INFO, string.format("aivmodel: a lord died: #%s", playerID))

      if pythonCallbacks['onLordKilled'] ~= nil then
        log(INFO, string.format("aivmodel: calling python callback onLordKilled"))

        local ret = pythonCallbacks['onLordKilled'](playerID)
        log(INFO, string.format("aivmodel: callback returned: %s", ret))
        if ret == 1 or ret == true then
          log(INFO, "aivmodel: restarting game")
          core.writeInteger(0x01126600, 0x2c)
          restart(0x16)
        elseif ret == 0 or ret == false then
          log(INFO, "aivmodel: not restarting the game")
        else
          log(INFO, "aivmodel: warning, did an error occur in Python?")
        end
      else
        log(INFO, "aivmodel: callback isn't set")
      end
    end, 0x0056dbe4, 7)
  end,

  disable = function(self) end,
}


-- local function storeCallbackAddresses() 

--   local py_AddModule = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyImport_AddModule"), 1, 0)
--   local py_main = py_AddModule(ucp.internal.registerString("__main__"))
--   if py_main == 0 then log(ERROR, "__main__ == NULL") end
--   local py_GetAttrString = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyObject_GetAttrString"), 2, 0)
--   local py_aivmodel = py_GetAttrString(py_main, ucp.internal.registerString("aivmodel"))  
--   if py_aivmodel == 0 then log(ERROR, "aivmodel == NULL") end
--   local py_addr_onLordKilled = py_GetAttrString(py_aivmodel, ucp.internal.registerString("addr_onLordKilled"))
--   if py_addr_onLordKilled == 0 then log(ERROR, "addr_onLordKilled == NULL") end
--   local py_PyLong = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyLong_AsLong"), 1, 0)
--   local addr_onLordKilled = py_PyLong(py_addr_onLordKilled)
--   if addr_onLordKilled == 0 then log(ERROR, "addr_onLordKilled == 0") end

--   onLordKilled = core.exposeCode(addr_onLordKilled, 1, 2) -- stdcall, WINFUNCTYPE
  
--   return addr_onLordKilled
-- end

-- local function setLuaRegisterCallbackAddress() 
--   local py_PyLong_FromLong = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyLong_FromLong"), 1, 0)
--   local py_long = py_PyLong_FromLong(registerCallbackLocation)
--   local py_AddModule = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyImport_AddModule"), 1, 0)
--   local py_main = py_AddModule(ucp.internal.registerString("__main__"))
--   if py_main == 0 then log(ERROR, "__main__ == NULL") end
--   local py_SetAttrString = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyObject_SetAttrString"), 3, 0)
--   return py_SetAttrString(py_main, ucp.internal.registerString("_LUA_REGISTER_CALLBACK_ADDRESS"), py_long)
-- end