import numpy as np
from pathlib import Path

from typing import Generator, Tuple

from .utils import BaseExporter
from . import config, mesh, depth, currents
    
class CSVExporter(BaseExporter):
    """
    Exporter class to write data to CSV files.
    """
    NAME = "csv"
    def __init__(self,config: config.Configuration) -> None:
        super().__init__(config)
    
    def merge_coords(self,m: mesh.BaseSegment) -> Generator[Tuple, None, None]:
        """Decompose mesh grid to 1d arrays of coordinates.
        """
        mx = np.hstack(m.xx)
        my = np.hstack(m.yy)
        mx: np.ndarray; my: np.ndarray # make typeck happy
        
        assert mx.shape == my.shape

        return zip(mx,my)

    def merge_metrics(
        self,depth: depth.DepthMap,
        currents: currents.CurrentMap) -> Generator[Tuple, None, None]:
        """
        Merge depth map and current map into a generator for further processing.
        """
        depth = np.hstack(depth) # Depth map
        cx = np.hstack(currents.x) # Current velocity in x direction
        cy = np.hstack(currents.y) # Current velocity in y direction
        cvel = np.sqrt(cx**2 + cy**2) # Resulting current velocity

        l = [depth,cx,cy,cvel]

        if not all(map(lambda x: x.shape == l[0].shape,l)):
            raise ValueError("Shapes of depth map and current maps do not match.")
        
        return zip(cy,cx,depth,cvel)

    def write_to_file(
        self,c_gen: Generator[Tuple, None, None],
        m_gen: Generator[Tuple, None, None],
        folder_name: Path) -> None:
        """Write to file.
        """
        with open(f"{folder_name}/coords.csv", "w") as f:
            header = "x [UTM32],y [UTM32]\n"
            f.write(header)
            for row in c_gen:
                f.write("{}, {}\n".format(*row))

        with open(f"{folder_name}/metrics.csv", "w") as f:
            header = (
                "water_depth [m],"
                "current_vel_x [m/s],"
                "current_vel_y [m/s],"
                "current_velocity [m/s]\n"
            )
            f.write(header)
            for row in m_gen:
                f.write("{}, {}, {}, {}\n".format(*row))
