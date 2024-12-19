import math
import numpy as np

from typing import TypeVar

from . import mesh
from .config import Configuration

DepthMap = TypeVar("DepthMap")

# Function to generate water depth according 
# to a flipped standard normal distribution
def depth_map(m: mesh.BaseSegment, config: Configuration) -> DepthMap:
    """
    Generate a map of depths sampled from a
    flipped normal distribution centered around 
    the mid-index of m. 

    Args:
        m (mesh.MeshGrid): MeshGrid Segment
        var (float): Standard normal variance 

    Returns:
        DepthMap: DepthMap of same shape as m
    """
    out = []
    def _wd_gen(x,steepness,location):
        return config.MAX_DEPTH*math.exp(
            -5e-5*steepness*(x+location)**4
        )
    
    depth_linspace = np.linspace(-15,15,config.GP) 

    ar1steepness = SmoothedAR1Process(
        0.995,0.005,config.VARIANCE*10,2.5,len(m.yy),0.01)
    ar1location = SmoothedAR1Process(
        0.99,0.01,config.VARIANCE*30,0,len(m.yy),0.05)
    ar1s = ar1steepness.generate()
    ar1l = ar1location.generate()
    
    for i in range(len(m.yy)):
        r = []
        for j in range(config.GP):
            r.append(_wd_gen(depth_linspace[j],ar1s[i],ar1l[i]))
        out.append(r)
    
    return out

class SmoothedAR1Process:
    """
    Autoregressive process of order 1
    """
    def __init__(self, 
                 ar1_rho: float, 
                 ar1_sigma: float,
                 ar1_variance: float,
                 ar1_start: float,
                 ar1_length: int,
                 exp_smoothing: float) -> None:
        self.ar1_rho = ar1_rho
        self.ar1_sigma = ar1_sigma
        self.ar1_start = ar1_start
        self.ar1_variance = ar1_variance
        self.ar1_prev = ar1_start
        self.ar1_length = ar1_length
        self.exp_smoothing = exp_smoothing
    
    def generate(self) -> np.ndarray:
        out = np.empty(self.ar1_length)
        out[0] = self.ar1_start
        for i in range(1,self.ar1_length):
            out[i] = self.ar1_rho*out[i-1] + self.ar1_sigma*np.random.normal(
                loc=self.ar1_start,scale=self.ar1_variance
            )
        return self.exp_smooth(out)
    
    def exp_smooth(self, ar1: np.ndarray) -> np.ndarray:
        out = np.empty(self.ar1_length)
        out[0] = ar1[0]
        for i in range(1,self.ar1_length):
            out[i] = self.exp_smoothing*ar1[i] + (1-self.exp_smoothing)*out[i-1]
        return out
    
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    ar1 = SmoothedAR1Process(0.99,0.01,20,2,1000,0.01)
    plt.plot(ar1.generate())
    plt.show()