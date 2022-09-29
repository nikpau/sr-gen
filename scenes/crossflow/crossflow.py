from matplotlib import cm
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

BPD = 20 # base point distance [m]
GP = 26 # grid points

CURRENT_SPEED = 1 # [m/s]

RIVER_LENGTH = 4000 # [m]

# Generate a straight river segment
# with a mesh grid
x = np.linspace(0, 500, GP)
y = np.linspace(0, RIVER_LENGTH, RIVER_LENGTH//BPD)

xx,yy  = np.meshgrid(x,y)

# Function to generate water depth according 
# to a flipped standard normal distribution
f = lambda x: 10*np.exp(-0.005*(x**2))
depth_linspace = np.linspace(-BPD,BPD,GP)
zz = [list(map(f,depth_linspace)) for _ in range(len(y))]

# Generate current map
empty = np.zeros((len(y),GP))
curr_x = np.zeros((len(y)//4,GP))
curr_y = np.full((len(y)//4,GP),CURRENT_SPEED)
curr_v = np.vstack([curr_x,curr_y,curr_x,curr_x])

# Save coords to csv
coords = pd.DataFrame(
    {
        "x":xx.flatten(), 
        "y":yy.flatten()
    }).to_csv(
        "scenes/crossflow/coords.txt", index=False,sep=" ",header=False)

metrics = pd.DataFrame(
    {
        "empty0":np.zeros_like(empty).flatten(),
        "curr_y":((curr_v/np.max(curr_v))*np.pi/2).flatten(),
        "curr_x":empty.flatten(),
        "depth":np.array([zz]).flatten().clip(min=0) ,
        "empty1":np.zeros_like(empty).flatten(),
        "empty2":np.zeros_like(empty).flatten(),
        "curr_speed":curr_v.flatten()
    }).to_csv("scenes/crossflow/metrics.txt", index=False,sep=" ",header=False)


plt.contourf(
    xx,yy,zz, 
    cmap = cm.ocean, 
    levels = np.linspace(-1,np.max(zz),50))

plt.quiver(xx,yy,curr_v,empty,color='w',scale = 200)

plt.show()