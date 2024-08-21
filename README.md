# stronghold-crusader-aivmodel
Tool to generate AI villages (castle designs) procedurally or using machine learning and AI

## Installation
1. Install the https://github.com/UnofficialCrusaderPatch/UnofficialCrusaderPatch
2. Install python 3.8 32-bit.
3. Install pymem, numpy, and the sourcehold module from https://github.com/Sourcehold/sourcehold-maps using `python -m pip install`

## Usage
Add the `ucp-aivmodel-*` extension to your ucp/modules folder (copy paste the directory).
Run using `python -m aivmodel`, which will start the game. 

When a lord dies in combat, an event is sent to python, asking to continue the game or restart it.

## To implement
Reading the scores of the AI in the game from python

### AI and Machine Learning
Implement algorithms to generate AI castles

Important aspect is detecting if an AIV is going to work, in terms of pathing for example.

#### Detecting building types
```py
import numpy as np
import cv2 as cv

def building_mask(size, normalize = True):
  m = np.zeros(((size*2)-1, (size*2)-1), dtype='uint8')
  m[(size-1):, (size-1):] = 1
  if normalize:
    m = m / (size*size)
  return m

# Detects buiildings of size 2
cv.filter2D(constructions, -1, building_mask(2), borderType=cv.BORDER_CONSTANT)
```
Note: doesn't work if two buildings of the same type are aligned next to each other. Maybe for loops are better...


#### Detecting invalid paths
1. Flood fill (not diagonally) from the campfire and the stockpile.  
    a. Note that gates should be passable (horizontally or vertically through the middle tile), small and large gates.
2. Check if the flood fill matrix and the exit matrix of an economic building have overlap.  
    a. Exit matrix is defined as the horizontal and vertical neighbour tiles of a workshop building.
3. If not, nudge the building in a possible direction and check again.
