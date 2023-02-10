from os import PathLike
from .config import ConfigFile, Configuration
from .export import export_to_file
import shutil
from .log import logger
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import csv

def _construct(configpath: str) -> tuple[PathLike,Configuration]:
    config = ConfigFile(configpath).export()
    return export_to_file(config), config

def _load(datapath: str):
    with open(f"{datapath}/coords.txt","r") as f:
        reader = csv.reader(f,delimiter=" ")
        coords = list(reader)

    with open(f"{datapath}/metrics.txt","r") as f:
        reader = csv.reader(f,delimiter=" ")
        metrics = list(reader)

    return metrics, coords

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

def rivergen_rndm_viz(configpath: str):
    """
    Constructs and shows a test river. 
    Deletes it afterwards.
    """
    logger.info("Initializing random river testing.")
    datapath,config = _construct(configpath)
    logger.info(
        f"River successfully constructed at '{datapath}'."
    )
    data = _load(datapath)
    _plot(*data,config)
    shutil.rmtree(datapath)
    logger.info(
        f"River successfully deleted at '{datapath}."
    )

def visualize(datapath: str, config: Configuration):
    data = _load(datapath)
    _plot(*data,config)