import numpy as np

from attr import define

from . import mesh
from .config import Configuration

@define
class CurrentMap:
    """Current map.
    """
    x: np.ndarray
    y: np.ndarray 

def current_map(m: mesh.BaseSegment, config: Configuration) -> CurrentMap:
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
    
    ones = np.ones_like(m.yy)
    xout, yout = np.empty_like(ones), np.empty_like(ones)

    # Create Gaussian profile across width (columns)
    width = ones.shape[1]
    x_coords = np.linspace(-2, 2, width)
    gaussian = np.exp(-x_coords**2)
    
    # Add lateral distortion with sine wave
    distortion = np.sin(np.linspace(0, 4*np.pi, ones.shape[0])) * 0.2 * config.MAX_VEL

    for row in range(ones.shape[0]):
        xout[row] = distortion[row]  # Lateral current distortion
        yout[row] = -gaussian * config.MAX_VEL  # Downstream Gaussian profile

    return CurrentMap(xout, yout)
