import itertools
import os
import sys
import threading
import time
import uuid
import numpy as np
from rivergen import mesh, depth, currents,config 
from .log import logger
from typing import Generator, Tuple

def merge_coords(m: mesh.BaseSegment) -> Generator[Tuple, None, None]:
    """Decompose mesh grid to 1d arrays of coordinates.
    """
    mx = np.hstack(m.xx)
    my = np.hstack(m.yy)

    assert mx.shape == my.shape

    return zip(mx,my)

def merge_metrics(d: depth.DepthMap,c: currents.CurrentMap) -> Generator[Tuple, None, None]:
    """Merge depth map and current map into a generator for further processing.
    """
    d = np.hstack(d) # Depth map
    cx = np.hstack(c.x) # Current velocity in x direction
    cy = np.hstack(c.y) # Current velocity in y direction
    cvel = np.sqrt(cx**2 + cy**2) # Resulting current velocity
    zeros = np.zeros_like(cx) # Special formatting (not needed)

    l = [d,cx,cy,cvel,zeros]

    if not all(map(lambda x: x.shape == l[0].shape,l)):
        raise ValueError("Shapes of depth map and current maps do not match.")
    
    return zip(zeros,cy,cx,d,zeros,zeros,cvel)

def write_to_file(
    coords: Generator[Tuple, None, None],
    metrics: Generator[Tuple, None, None],
    folder_name: os.PathLike) -> None:
    """Write to file.
    """
    with open(f"{folder_name}/coords.txt", "w") as f:
        for row in coords:
            f.write("{} {}\n".format(*row))

    with open(f"{folder_name}/metrics.txt", "w") as f:
        for row in metrics:
            f.write("{} {} {} {} {} {} {}\n".format(*row))

def export_to_file(config: config.Configuration) -> os.PathLike:
    """
    Package main function. Generates xy 
    coordinates, depths and current fields
    from randomly sized curves and lines. 
    Saves the output as whitespace separated 
    `.txt` file in a folder named by a random 
    hexadecimal string in the modules root.
    
    The files containing coordinates (coords.txt)
    have two columns [x,y].
    (metrics.txt) has seven colums 
    [_, current_vel_y,current_vel_x,water_depth, _, _, current_velocity]
    
    This format is currently very specific. In order to change it
    see the `merge_metrics()` function

    Args:
        segments (int): Number of segments making up the river/road
        var (float): Variability of depth distribution
        vel (float): maximum current velocity

    Returns:
        os.PathLike: path to folder containing generated files
    """

    parent = "gen"
    
    # Check if `gen` folder exists. If not, create it.
    if not os.path.isdir(parent):
        os.mkdir(parent)

    # Create folder
    folder_name = uuid.uuid4().hex
    filepath = f"{parent}/{folder_name}"
    os.mkdir(filepath)

    # Generate mesh
    builder = mesh.Builder(config)
    m = builder.generate(f"{parent}/{folder_name}/Segments")
    if config.VERBOSE:
        logger.info("Mesh generated.")

    # Generate depth map
    d = depth.depth_map(m,config)
    if config.VERBOSE:
        logger.info("Depth map generated.")

    # Generate current map
    c = currents.current_map(m,config)
    if config.VERBOSE:
        logger.info("Current map generated.")

    # Merge coordinates and metrics
    coords = merge_coords(m)
    metrics = merge_metrics(d,c)
    if config.VERBOSE:
        logger.info("Merged.")

    # Loading animation
    done = False
    def animate():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if done:
                break
            print('Writing to file... ' + c,end="\r")
            sys.stdout.flush()
            time.sleep(0.1)
    if config.VERBOSE:
        t = threading.Thread(target=animate)
        t.start()

    # Write to file
    write_to_file(coords,metrics,filepath)

    done = True

    return filepath