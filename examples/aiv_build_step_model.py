from aivmodel.handler import Handler

class AIVBuildStepHandler(Handler):

  def __init__(self):
    super().__init__()

  def initialize(self):
    import numpy
    super().initialize()

  def onLordKilled(self, playerID):
    print("lord killed, what to do now?")
    return super().onLordKilled(playerID)
  
HANDLER = AIVBuildStepHandler()