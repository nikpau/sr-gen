import rivergen as rg
from rivergen import options as op
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import csv

rg.options.GP = 26
path = rg.export_to_file(10,2,op.MAX_VEL)

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
plt.contourf(xx,yy,wd,cmap=cm.ocean,levels = np.linspace(0,np.max(wd),10))
#plt.quiver(xx,yy,cx,cy,scale = 100)
plt.tight_layout()
plt.axis("equal")
plt.show()