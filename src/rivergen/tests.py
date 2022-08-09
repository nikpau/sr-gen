import rivergen as rg
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

m = rg.mesh.generate(10)
d = rg.depth.depth_map(m,1)
c = rg.currents.current_map(m,1.5)

#plt.scatter(m.xx,m.yy,c=d,cmap=cm.gray)
plt.contourf(m.xx,m.yy,d,cmap=cm.ocean,levels = np.linspace(0,np.max(d),20))
#plt.quiver(m.xx,m.yy,c.x,c.y,scale = 100)
plt.axis("equal")
plt.show()