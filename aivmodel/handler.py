class Handler(object):

  def __init__(self):
    super().__init__()
    self.initialized = False

  def initialize(self):
    """
    Do expensive initialization here, called upon first use
    """
    self.initialized = True

  def onLordKilled(self, playerID):
    """
      Implement your logic here, return True to restart the game, return False to let the game continue to run
    """
    return False