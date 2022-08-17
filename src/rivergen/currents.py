from dataclasses import dataclass
import numpy as np
from . import mesh

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
        CurrentMap: Current of same x or y shape as imput segment.
    """
    
    ones= np.ones_like(m.yy)
    xout, yout = np.empty_like(ones), np.empty_like(ones)

    linx = np.linspace(-v,v,ones.shape[0])
    linx = list(map(np.sin,linx))

    liny = np.linspace(0,v,ones.shape[0])

    for row in range(ones.shape[0]):
        xout[row] = ones[row] * linx[row]
        yout[row] = ones[row] * -liny[row]

    return CurrentMap(xout, yout)
