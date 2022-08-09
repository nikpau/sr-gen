import mesh
import depth
import currents
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

m = mesh.generate(30)
d = depth.depth_map(m,2)
cx,cy = currents.current_map(m)

#plt.scatter(m.xx,m.yy,c=d,cmap=cm.gray)
plt.contourf(m.xx,m.yy,d,cmap=cm.ocean,levels = np.linspace(0,np.max(d),20))
plt.quiver(m.xx,m.yy,cx,cy,scale = 100)
plt.axis("equal")
plt.show()