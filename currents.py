from typing import TypeVar
from matplotlib import cm

import numpy as np 
import mesh
import depth
import matplotlib.pyplot as plt

CurrentMap = TypeVar("CurrentMap")

def current_map(m: mesh.Segment) -> CurrentMap:
    
    ones= np.ones_like(m.yy)
    xout, yout = np.empty_like(ones), np.empty_like(ones)

    lin = np.linspace(-2,2,ones.shape[0])
    lin = list(map(np.sin,lin))

    for row in range(ones.shape[0]):
        xout[row] = ones[row] * lin[row]
        yout[row] = ones[row] * -lin[row]

    return xout,yout