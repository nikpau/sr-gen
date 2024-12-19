import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

from typing import Generator, Tuple

from .utils import BaseExporter, logger
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
                
class UCDExporter(BaseExporter):
    """
    Exporter class to write the generated
    data as an AVS-UCD (Unstructured Cell Data) file.
    """
    NAME = "ucd"
    EOL = "\r\n"
    def __init__(self,config: config.Configuration) -> None:
        super().__init__(config)
    
    def merge_coords(self,m: mesh.BaseSegment) -> np.ndarray:
        """
        Decompose mesh grid to 1d arrays of coordinates.
        We output a 2D array with x and y coordinates instead
        of a generator as we need these values two times:
        1. For the coordinates file
        2. For the mesh triangulation
        """
        mx = np.hstack(m.xx)
        my = np.hstack(m.yy)
        mz = np.zeros_like(mx)
        mx: np.ndarray; my: np.ndarray
        
        assert mx.shape == my.shape == mz.shape
        
        return np.array([mx,my,mz]).T
    
    def _header(self) -> str:
        msg1 = (
            "# AVS-UCD FILE CREATED BY "
            "SEG-GEN "
            f"at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{self.EOL}"
        )
        return msg1
    
    def _define_mesh(self, tri: np.ndarray, coords: np.ndarray) -> str:
        trsh = tri.shape[0]
        return f"{coords.shape[0]} {trsh} 3 0 0{self.EOL}"
    
    def _variable_definition(self) -> str:
        return f"2 2 1{self.EOL}UV,m/s{self.EOL}S,mNN{self.EOL}"
    
    def merge_metrics(
        self,depth: depth.DepthMap,
        currents: currents.CurrentMap) -> np.ndarray:
        """
        Merge depth map and current map into a generator for further processing.
        """
        depth = np.hstack(depth)
        cx = np.hstack(currents.x)
        cy = np.hstack(currents.y)
        
        l = [depth,cx,cy]
    
        if not all(map(lambda x: x.shape == l[0].shape,l)):
            raise ValueError("Shapes of depth map and current maps do not match.")  
        
        self.metrics = np.array([cy,cx,depth]).T
        return self.metrics
    
    def _triangulate(self, coords: np.ndarray) -> np.ndarray:
        """
        Perform a simplified Delaunay triangulation of the river coordinates
        by exploiting the regular structure of the river grid.
        """
        logger.info("Performing simplified triangulation.")
        RLEN = self.config.GP  # Number of columns in the grid

        # Calculate the number of rows
        nrows = coords.shape[0] // RLEN

        # Create a grid of indices
        idx = np.arange(coords.shape[0]).reshape(nrows, RLEN)

        # Exclude the last row and last column to avoid index out of bounds.
        # Add 1 to account for one-indexing in UCD files.
        idx_i = idx[:-1, :-1] + 1 # Lower left corner of each cell
        idx_i1 = idx[:-1, 1:] + 1 # Lower right corner of each cell
        idx_RLEN = idx[1:, :-1] + 1 # Upper left corner of each cell
        idx_RLEN1 = idx[1:, 1:] + 1 # Upper right corner of each cell

        # Flatten the indices
        idx_i_flat = idx_i.ravel()
        idx_i1_flat = idx_i1.ravel()
        idx_RLEN_flat = idx_RLEN.ravel()
        idx_RLEN1_flat = idx_RLEN1.ravel()

        # Lower triangles: [i, i+1, i+RLEN]
        lower_triangles = np.stack(
            [idx_i_flat, idx_i1_flat, idx_RLEN_flat], 
            axis=1
        )

        # Upper triangles: [i+1, i+RLEN, i+RLEN+1]
        upper_triangles = np.stack(
            [idx_i1_flat, idx_RLEN_flat, idx_RLEN1_flat], 
            axis=1
        )

        # Combine lower and upper triangles
        vertex_indices = np.vstack(
            [lower_triangles, upper_triangles]
        )

        return vertex_indices

    def write_to_file(
        self, 
        coords_in: np.ndarray,
        metrics_in: np.ndarray,
        folder_name: Path) -> None:
        """Write to file."""
        
        # Perform Constrained Delaunay Triangulation
        self.tri = self._triangulate(coords_in)
        
        # # The CDT imposes a new order on the vertices, 
        # # so we need to reorder the metrics and coordinates
        # ro_idx = self._reorder_map(coords_in,self.tri)
        self.metrics = metrics_in
        self.coords = coords_in

        # Generate indices for the nodes
        indices = np.arange(1, self.tri.shape[0] + 1)
        
        # Prepare data for the UCD file
        meshdef = self._define_mesh(self.tri, self.coords)

        with open(f"{folder_name}/generated.inp", "w") as f:
            f.write(self._header())

            # Write the mesh definition
            f.write(meshdef)

            # Prepare and write node data
            node_lines = [f"{int(idx)} {row[0]} {row[1]} {row[2]}{self.EOL}" 
                          for idx, row in zip(indices,self.coords)]
            f.writelines(node_lines)

            # Prepare and write mesh data
            mesh_lines = [ # v-------------material
                f"{int(idx)} 1 tri {row[0]} {row[1]} {row[2]}{self.EOL}"
                for idx, row in zip(indices, self.tri)
            ]
            f.writelines(mesh_lines)

            # Write the variable definition
            f.write(self._variable_definition())

            # Prepare and write metric data
            metric_lines = [
                f"{int(idx)} {row[0]} {row[1]} {row[2]}{self.EOL}"
                for idx, row in zip(indices,self.metrics)
            ]
            f.writelines(metric_lines)
            
    def plot_contour(self):
        """
        Creates a contour plot of the generated mesh
        and the associated metrics.
        """
        x = self.coords[:,0].reshape(-1,self.config.GP)
        y = self.coords[:,1].reshape(-1,self.config.GP)
        wd = self.metrics[:,2].reshape(-1,self.config.GP)
        
        # Create a matplotlib figure and axes
        fig, ax = plt.subplots(figsize=(8, 6))
        ax: plt.Axes
        ax.contourf(x, y, wd, cmap='ocean', levels=20)
        ax.set_xlabel('X-coordinate')
        ax.set_ylabel('Y-coordinate')
        ax.set_title('Water Depth Contour Plot')
        
        plt.tight_layout()
        plt.show()
                
    def plot_triangulation(
        self, show_points=True, show_triangles=True, 
        point_labels=False, point_color='red', 
        line_color='blue', point_size=5, line_width=0.5):
        """
        Plot Delaunay triangulation with additional features.
        """
        points = self.coords[:,:2]
        
        # Create a matplotlib figure and axes
        fig, ax = plt.subplots(figsize=(8, 6))
        ax: plt.Axes
        
        if show_triangles:
            # Plot the triangulation edges
            ax.triplot(points[:, 0], points[:, 1], self.tri - 1,
                       color=line_color, linewidth=line_width)
        
        if show_points:
            # Plot the points
            ax.plot(
                points[:, 0], points[:, 1], 
                'o', color=point_color, markersize=point_size)
        
            if point_labels:
                # Annotate points with their indices
                for i, (x, y) in enumerate(points):
                    ax.text(x, y, str(i), fontsize=8, ha='right')
        
        # Set labels and title
        ax.set_xlabel('X-coordinate')
        ax.set_ylabel('Y-coordinate')
        ax.set_title('Delaunay Triangulation')
        ax.set_aspect('equal')
        plt.tight_layout()
        plt.show()

class FlatProjectionBinaryWaterdepthExporter(BaseExporter):
    """
    Projects the generated river's water depth to a flat plane
    and exports it as a binary map depending on some threshold.
    
    A chooseble threshold is used to determine the water depth
    cutoff, i.e. all water depths below this threshold are
    considered dry. After the projection, the water depth
    is exported as a binary map, meaning that all water depths
    below the threshold are set to zero and all water depths
    above the threshold are set to one.
    """
    NAME = "flatbin"
    
    def __init__(self,config: config.Configuration) -> None:
        super().__init__(config)
    
    def merge_coords(self,m: mesh.BaseSegment) -> None:
        """
        Coordinates are not needed for this exporter.
        """
        return None
    
    def merge_metrics(
        self,depth: depth.DepthMap,
        currents: currents.CurrentMap) -> Generator[Tuple, None, None]:
        """
        The exporter only relies on the depth map to create the binary map.
        All other metrics are ignored.
        """
        return np.hstack(depth) # Depth map
    
    def export(self,threshold: float) -> np.ndarray:
        """
        Export the water depth as a binary map, where all water depths
        below the threshold are set to zero and all water depths above
        the threshold are set to one.
        """
        _, wd = self.construct()
        wd = np.where(wd < threshold,0,1)
        
        # Project the water depth to a flat plane
        width = self.config.GP
        
        wd = wd.reshape(-1,width)

        return wd

    def construct(self) -> Generator[Tuple, None, None]:
        """
        Main construction function. Generates xy 
        coordinates, depths and current fields
        from randomly sized curved and straight
        segments, according to the configuration
        file. 
        
        The output is generated according to the
        specified exporter in the configuration
        file.
        The folder name is a random hexadecimal 
        string.
        
        The output is saved as a whitespace separated 
        `.txt` file in a folder named by a random 
        hexadecimal string in the modules root.

        Returns:
            os.PathLike: path to folder containing 
            generated files
        """

        # Generate mesh
        builder = mesh.Builder(self.config)
        m = builder.generate()
        if self.config.VERBOSE:
            logger.info("Mesh generated.")

        # Generate depth map
        d = depth.depth_map(m,self.config)
        if self.config.VERBOSE:
            logger.info("Depth map generated.")

        # Generate current map
        c = currents.current_map(m,self.config)
        if self.config.VERBOSE:
            logger.info("Current map generated.")

        # Merge coordinates and metrics
        coords = self.merge_coords(m)
        metrics = self.merge_metrics(d,c)
        if self.config.VERBOSE:
            logger.info("Merged.")

        return coords, metrics

    def write_to_file(self, c_gen, m_gen, folder_name):
        raise NotImplementedError("This exporter does not support writing to file.")