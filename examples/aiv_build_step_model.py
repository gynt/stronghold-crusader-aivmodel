from aivmodel.handler import Handler
from aivmodel import set_handler
import win32api
import win32con
import traceback

from sourcehold.aivs import AIV

import random
import numpy, math

import pathlib

INTERACTIVE = True

class AIVInterface(AIV):
  def __init__(self, path, iteration = None):
    super().__init__()
    self.iteration = 0
    if iteration is not None:
      self.iteration = iteration
    self.path = path
    self.from_file(path)
    #self.original_steps_data = self.directory[2008].get_data()
    #self.original_constructions_data = self.directory[2007].get_data()
  # def restore_original(self):
    # self.directory[2008].set_data(self.original_steps_data)
    # self.directory[2007].set_data(self.original_constructions_data)
    # self.save()
  def save(self):
    self.to_file(self.path)
  def store(self):
    p = pathlib.Path(self.path + "." + str(self.iteration))
    if p.exists() and INTERACTIVE:
      answer = win32api.MessageBox(None, f"Iteration {self.iteration} already exists, overwrite?", "Duplicate iteration", win32con.MB_OKCANCEL)
      if not answer:
        return
    self.to_file(str(p))
  def get_steps(self):
    matrix = numpy.frombuffer(self.directory[2008].get_data(), dtype='uint32')
    matrix.shape = (100, 100)
    return matrix.copy() # Otherwise it is read only...
  def _distance(self, stepsCount, learning_rate, learning_rate_unit):
    if learning_rate_unit == "relative":
      learning_rate = (learning_rate * stepsCount) // 100
    randomValueBetween0and1 = random.betavariate(2, 2) # normally distributed somewhat...
    distance = (randomValueBetween0and1 - 0.5) * learning_rate
    return distance
  def swap_steps(self, learning_rate = 10, learning_rate_unit = "percentage"):
    """
      Swap 2 steps.
      Learning rate defines the maximum distance between the steps.
      Can be defined as absolute and relative.
    """
    steps_matrix = self.get_steps()
    steps = sorted(v for v in set(steps_matrix.flat))
    step_min = min(steps)
    step_max = max(steps)
    distance = self._distance(len(steps), learning_rate=learning_rate, learning_rate_unit=learning_rate_unit)
    step1 = random.choice(steps)
    for _ in range(1000):
      step2 = step1 + math.ceil(distance)
      if step2 < step_min:
        step2 = step_min
      if step2 > step_max:
        step2 = step_max
      if step2 in steps:
        break  
      step1 = random.choice(steps)
    else:
      raise Exception("reached limit, steps impossible")
    step1x, step1y = numpy.where(steps_matrix == step1)
    step2x, step2y = numpy.where(steps_matrix == step2)
    steps_matrix[step1x, step1y] = step2
    steps_matrix[step2x, step2y] = step1
    self.directory[2008].set_data(steps_matrix.tobytes())
    if INTERACTIVE:
      win32api.MessageBox(None, f"Original step {step1} is swapped with step: {step2}", "Test", win32con.MB_OK)
  def swap_multiple_steps(self, n, learning_rate = 10, learning_rate_unit = "percentage"):
    for _ in range(n):
      self.swap_steps(learning_rate=learning_rate, learning_rate_unit=learning_rate_unit)
  def relocate_step(self, learning_rate = 10, learning_rate_unit = "percentage"):
    """
      Moves a step at a new location
    """
    steps_matrix = self.get_steps()
    steps = sorted(v for v in set(steps_matrix.flat))
    step_min = min(steps)
    step_max = max(steps)
    distance = self._distance(len(steps), learning_rate=learning_rate, learning_rate_unit=learning_rate_unit)
    step1 = random.choice(steps)
    for i in range(1000):
      step2 = step1 + math.ceil(distance)
      if step2 < step_min:
        step2 = step_min
      if step2 > step_max:
        step2 = step_max
      if step2 in steps:
        break  
      step1 = random.choice(steps)
    else:
      raise Exception("reached limit, steps impossible")
    raise NotImplementedError("more difficult than I thought")
    self.directory[2008].set_data(steps_matrix.tobytes())
  def next_iteration(self):
    self.iteration += 1
    self.swap_steps()
    self.save()
    self.store()
  def previous_iteration(self):
    self.iteration -= 1
    self.from_file(self.path + '.' + str(self.iteration))

saladin = AIVInterface("C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stronghold Crusader Extreme\\ucp\\plugins\\Vanilla-Interpretation-Castles-Remodeled-1.0.2\\resources\\ai\\saladin\\aiv\\saladin6.aiv")

class AIVBuildStepSolver(Handler):

  def __init__(self):
    super().__init__()
    self.wins = {}
    self.losses = {}
    self.retries = 3

  def initialize(self):
    super().initialize()

  def onLordKilled(self, playerID):
    try:
      if playerID == 0:
        return win32api.MessageBox(None, f"Test!", "Test", win32con.MB_OKCANCEL)
      win = playerID == 2 # Assuming 1 vs 1 and ai player was placed in slot 1
      iteration = saladin.iteration
      if iteration not in self.losses:
        self.losses[iteration] = 0
      if iteration not in self.wins:
        self.wins[iteration] = 0

      if win:
        self.wins[iteration] += 1
      if not win:
        self.losses[iteration] += 1
      
      if iteration < 1:
        if INTERACTIVE:
          win32api.MessageBox(None, f"Next iteration!", "Choice:", win32con.MB_OKCANCEL)
        saladin.next_iteration()
        return True
      
      previous = iteration - 1
      if (self.wins[previous] - self.losses[previous]) > (self.wins[iteration] - self.losses[iteration]):
        if self.retries == 0:
          if INTERACTIVE and win32api.MessageBox(None, f"Previous iteration!", "Choice:", win32con.MB_OKCANCEL):
            saladin.previous_iteration()
            self.retries = 3 # For next time we lose
          else:
            self.retries = 1
        else:
          self.retries -= 1 # Keep the current aiv once more
      else:
        # Keep developing this aiv
        if INTERACTIVE and win32api.MessageBox(None, f"Next iteration!", "Choice:", win32con.MB_OKCANCEL):
          saladin.next_iteration()


      # Restart the game!
      return True
    except Exception as e:
      win32api.MessageBox(None, f"{e}", "Error in build step model:", win32con.MB_OK)
      win32api.MessageBox(None, f"{''.join(traceback.TracebackException.from_exception(e).format())}", "Error in build step model:", win32con.MB_OK)
      return False
  
set_handler(AIVBuildStepSolver())