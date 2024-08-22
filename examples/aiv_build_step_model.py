from aivmodel.handler import Handler
from aivmodel import set_handler
import win32api
import win32con

from sourcehold.aivs import AIV

saladin1 = AIV().from_file("C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stronghold Crusader Extreme\\aiv\\saladin1.aiv")

class AIVBuildStepSolver(Handler):

  def __init__(self):
    super().__init__()

  def initialize(self):
    import numpy
    super().initialize()

  def onLordKilled(self, playerID):
    print("lord killed, what to do now?")
    answer = win32api.MessageBox(None, f"Player #{playerID} died.\nWhat to do now?", "A lord died!", win32con.MB_OKCANCEL)
    return answer
  
set_handler(AIVBuildStepSolver())