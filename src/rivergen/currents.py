from dataclasses import dataclass
from typing import TypeVar
import numpy as np
import mesh

@dataclass
class CurrentMap:
    """Current map.
    """
    x: np.ndarray
    y: np.ndarray 

def current_map(m: mesh.Segment, v: float) -> CurrentMap:
    """Generate a current map for a given mesh.
    Current direction follows a sinusoidal pattern
    over the length of the segment. Speed ranges
    from -v to +v

    Args:
        m (mesh.Segment): Segment to generate current map for.
        v (float): maximum speed of the current

    Returns:
        CurrentMap: Curren of same x or y shape as imput segment.
    """
    
    ones= np.ones_like(m.yy)
    xout, yout = np.empty_like(ones), np.empty_like(ones)

    lin = np.linspace(-v,v,ones.shape[0])
    lin = list(map(np.sin,lin))

    for row in range(ones.shape[0]):
        xout[row] = ones[row] * lin[row]
        yout[row] = ones[row] * -lin[row]

    return CurrentMap(xout, yout)
