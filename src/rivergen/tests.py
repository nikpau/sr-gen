import rivergen as rg
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import csv

rg.options.GP = 31
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

cy = np.array([row[1] for row in metrics],dtype=float)
cy = cy.reshape(-1,rg.options.GP)

cx = np.array([row[2] for row in metrics],dtype=float)
cx = cx.reshape(-1,rg.options.GP)

wd = np.array([row[3] for row in metrics],dtype=float)
wd = wd.reshape(-1,rg.options.GP)


#plt.scatter(xx,yy,c=wd,cmap=cm.turbo, marker="1")
plt.contour(xx,yy,wd,cmap=cm.turbo,levels = np.linspace(0,np.max(wd),10))
#plt.quiver(xx,yy,cx,cy,scale = 100)
plt.axis("equal")
plt.show()