from os import PathLike
import shutil
import rivergen as rg
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import csv

def _load(configpath: str) -> PathLike:
    config = rg.config.ConfigFile(configpath).export()
    path = rg.export_to_file(config)

    with open(f"{path}/coords.txt","r") as f:
        reader = csv.reader(f,delimiter=" ")
        coords = list(reader)

    with open(f"{path}/metrics.txt","r") as f:
        reader = csv.reader(f,delimiter=" ")
        metrics = list(reader)

    return metrics, coords, config, path

def _plot(metrics, coords, config):
    # Coordinate grid
    xx = np.array([row[0] for row in coords],dtype=float).reshape(-1,config.GP)
    yy = np.array([row[1] for row in coords],dtype=float).reshape(-1,config.GP)

    # Currents [not used for plotting]
    cy = np.array([row[1] for row in metrics],dtype=float).reshape(-1,config.GP)
    cx = np.array([row[2] for row in metrics],dtype=float).reshape(-1,config.GP)

    # Water depth
    wd = np.array([row[3] for row in metrics],dtype=float).reshape(-1,config.GP)


    plt.contourf(xx,yy,wd,cmap=cm.ocean,levels = np.linspace(0,np.max(wd),10))
    plt.tight_layout()
    plt.axis("equal")
    plt.show()

def rivergen_test(configpath: str):
    """
    Constructs and shows a test river. 
    Deletes it afterwards.
    """
    *data, path = _load(configpath)
    _plot(*data)
    shutil.rmtree(path)