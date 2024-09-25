import csv
import shutil
import numpy as np

from matplotlib import cm
import matplotlib.pyplot as plt

from .utils import logger, ConfigFile
from .config import Configuration

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
    cy = np.array([row[0] for row in metrics],dtype=float).reshape(-1,config.GP)
    cx = np.array([row[1] for row in metrics],dtype=float).reshape(-1,config.GP)

    # Water depth
    wd = np.array([row[2] for row in metrics],dtype=float).reshape(-1,config.GP)


    plt.contourf(xx,yy,wd,cmap=cm.ocean,levels = np.linspace(0,np.max(wd),20))
    plt.tight_layout()
    plt.axis("equal")
    plt.show()

def rivergen_rndm_viz(configpath: str):
    """
    Constructs and shows a test river. 
    Deletes it afterwards.
    """
    logger.info("Initializing random river testing.")
    c = ConfigFile(configpath)
    config = c.config
    exporter = c.export()
    datapath = exporter.export_to_file()
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