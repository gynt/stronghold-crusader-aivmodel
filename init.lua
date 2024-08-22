local callback_address_location = 0x004865fb -- code cave
local callback = nil

local _restart = core.exposeCode(0x00494950, 1, 0)
local restart = function()
  core.writeInteger(0x01126600, 0x2c)
  _restart(0x16)
end

local ptrCurrentUnitID = 0x00ee0fc8

local pythonDLL

local onLordKilled

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
  if filePath == nil or filePath:len() == 0 then
    log(WARNING, "No python file set")
    return
  end

  local runSimpleFileAddr = ucp.internal.getProcAddress(pythonDLL, "PyRun_SimpleFile")
  local runSimpleFile = core.exposeCode(runSimpleFileAddr, 2, 0)
  local filePointer = io.openFilePointer(filePath, 'rb')
  local filePathString = ucp.internal.registerString(filePath:match("([^\\/]*)[.]py$") or filePath)

  return runSimpleFile(filePointer, filePathString)
end

local function storeCallbackAddresses() 

  local py_AddModule = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyImport_AddModule"), 1, 0)
  local py_main = py_AddModule(ucp.internal.registerString("__main__"))
  if py_main == 0 then log(ERROR, "__main__ == NULL") end
  local py_GetAttrString = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyObject_GetAttrString"), 2, 0)
  local py_aivmodel = py_GetAttrString(py_main, ucp.internal.registerString("aivmodel"))  
  if py_aivmodel == 0 then log(ERROR, "aivmodel == NULL") end
  local py_addr_onLordKilled = py_GetAttrString(py_aivmodel, ucp.internal.registerString("addr_onLordKilled"))
  if py_addr_onLordKilled == 0 then log(ERROR, "addr_onLordKilled == NULL") end
  local py_PyLong = core.exposeCode(ucp.internal.getProcAddress(pythonDLL, "PyLong_AsLong"), 1, 0)
  local addr_onLordKilled = py_PyLong(py_addr_onLordKilled)
  if addr_onLordKilled == 0 then log(ERROR, "addr_onLordKilled == 0") end

  onLordKilled = core.exposeCode(addr_onLordKilled, 1, 2) -- stdcall, WINFUNCTYPE
  
  return addr_onLordKilled
end

return {
  enable = function(self, config)

    if config.enabled ~= true then return end

    log(VERBOSE, "initialize python: " .. (config.pythonDLLPath or ""))
    log(VERBOSE, initializePython(config.pythonDLLPath))

    local aivmodelBase = ucp.internal.resolveAliasedPath("ucp/modules/ucp-aivmodel/")
   -- Monkey patch
    log(VERBOSE, "import aivmodel")
    log(VERBOSE, executePythonString([[
import sys

# Insert a place to find modules from
sys.path.insert(0, "]] .. aivmodelBase .. [[")

# import main aivmodel so we can catch any imports here already
import aivmodel
    ]]))

    log(VERBOSE, "read aivmodel callback addresses")
    log(VERBOSE, string.format("%X", storeCallbackAddresses()))

    log(VERBOSE, "execute python file: " .. (config.pythonFilePath or ""))
    log(VERBOSE, executePythonFile(config.pythonFilePath))

    core.detourCode(function(registers)
      local unitID = core.readInteger(ptrCurrentUnitID)
      local playerID = core.readSmallInteger(0x013885e2 + (0x490 * unitID))

      log(INFO, string.format("aivmodel: a lord died: #%s", playerID))

      if onLordKilled ~= nil then
        log(INFO, string.format("aivmodel: calling python callback onLordKilled"))

        local ret = onLordKilled(playerID)
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
