import rivergen as rg
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import csv

path = rg.build(20,1,1.5)

with open(f"{path}/coords.txt","r") as f:
    reader = csv.reader(f,delimiter=" ")
    coords = list(reader)

with open(f"{path}/metrics.txt","r") as f:
    reader = csv.reader(f,delimiter=" ")
    metrics = list(reader)

xx = np.array([row[0] for row in coords],dtype=float)
xx = xx.reshape(-1,rg.options.GP)

yy = np.array([row[1] for row in coords],dtype=float)
yy = yy.reshape(-1,rg.options.GP)

wd = np.array([row[3] for row in metrics],dtype=float)
wd = wd.reshape(-1,rg.options.GP)


#plt.scatter(m.xx,m.yy,c=d,cmap=cm.ocean, marker=",")
plt.contourf(xx,yy,wd,cmap=cm.ocean,levels = np.linspace(0,np.max(wd),20))
#plt.quiver(m.xx,m.yy,c.x,c.y,scale = 100)
plt.axis("equal")
plt.show()