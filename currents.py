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

m = mesh.generate(30)
d = depth.depth_map(m,2)
cx,cy = current_map(m)

#plt.scatter(m.xx,m.yy,c=d,cmap=cm.gray)
plt.contourf(m.xx,m.yy,d,cmap=cm.ocean,levels = np.linspace(0,np.max(d),20))
plt.quiver(m.xx,m.yy,cx,cy,scale = 100)
plt.axis("equal")
plt.show()