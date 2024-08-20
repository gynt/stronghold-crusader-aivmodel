local callback_address_location = 0x004865fb -- code cave
local callback = nil

local _restart = core.exposeCode(0x00494950, 1, 0)
local restart = function()
  core.writeInteger(0x01126600, 0x2c)
  _restart(0x16)
end

local ptrCurrentUnitID = 0x00ee0fc8


return {
  enable = function(self)
    core.detourCode(function(registers)
      local unitID = core.readInteger(ptrCurrentUnitID)
      local playerID = core.readSmallInteger(0x013885e2 + (0x490 * unitID))

      log(INFO, string.format("aivmodel: a lord died: #%s", playerID))

      if string.format("%X%X%X%X", table.unpack(core.readBytes(callback_address_location, 4))) ~= "CCCCCCCC" then
        log(INFO, string.format("aivmodel: calling callback at: %X", core.readInteger(callback_address_location)))

        if callback == nil then
          callback = core.exposeCode(core.readInteger(callback_address_location), 1, 2) -- stdcall, WINFUNCTYPE
        end

        local ret = callback(playerID)
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
