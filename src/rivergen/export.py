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
        
        return np.array([cy,cx,depth]).T
    
    def mesh_boundary(self, coords: np.ndarray) -> np.ndarray:
        """
        Constructs the boundary polygon of the mesh by connecting 
        the outer points of each cross-section.

        Parameters
        ----------
        coords : np.ndarray
            An array of coordinates with shape (N, M), where N is 
            the total number of points, and M >= 3.
            Columns 0 and 1 (indices 0 and 1) correspond to the x 
            and y coordinates respectively.

        Returns
        -------
        boundary : np.ndarray
            An array of shape (P, 2), where P is the number of boundary 
            points plus one (for closing the polygon).
            Each row contains the (x, y) coordinates of a boundary point.

        Notes
        -----
        The boundary polygon is constructed by:
        - Taking the first cross-section as the lower boundary.
        - Connecting the outer (border) points (first and last points) 
        of each intermediate cross-section to form the sides.
        - Taking the last cross-section in reverse order as the upper 
            boundary.
        - Finally, the polygon is closed by returning to the starting 
            point.

        The array `coords` is expected to be organized such that it 
        can be reshaped into cross-sections,
        each containing `self.config.GP` points. The total number of 
        points should be divisible by `self.config.GP`.

        Examples
        --------
        >>> # Assuming self.config.GP = 4 (number of points per cross-section)
        >>> coords = np.array([
        ...     [x1_1, y1_1, z1_1],
        ...     [x1_2, y1_2, z1_2],
        ...     [x1_3, y1_3, z1_3],
        ...     [x1_4, y1_4, z1_4],
        ...     [x2_1, y2_1, z2_1],
        ...     # More points...
        ... ])
        >>> boundary = self.mesh_boundary(coords)
        """
        logger.info("Constructing mesh boundary.")
        # The shell of the polygon consists of the first and
        # last cross section of the river as well as the border
        # points of each other cross section.
        xy = coords[:,:2]
        
        # Reshape xy array
        xy = xy.reshape((-1,self.config.GP,2))

        # Get the number of boundary points
        n = 2*self.config.GP + 2*(xy.shape[0]-2)
        
        boundary = np.zeros((n+1,2))
        boundary[-1] = xy[0][0] # Close the polygon
        
        # Lower boundary
        boundary[:self.config.GP] = xy[0]

        # First side
        i = self.config.GP
        for k in range(1,xy.shape[0]-1):
            boundary[i] = xy[k][-1]
            i += 1
            
        # Upper boundary
        boundary[i:i+self.config.GP] = xy[-1][::-1]
        i+= self.config.GP
        
        # Second side
        for k in reversed(range(1,xy.shape[0]-1)):
            boundary[i] = xy[k][0]
            i+=1

        return boundary
    
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

        # Exclude the last row and last column to avoid index out of bounds
        idx_i = idx[:-1, :-1] # Lower left corner of each cell
        idx_i1 = idx[:-1, 1:] # Lower right corner of each cell
        idx_RLEN = idx[1:, :-1] # Upper left corner of each cell
        idx_RLEN1 = idx[1:, 1:] # Upper right corner of each cell

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

    
    def _reorder_map(self,coords: np.ndarray,tri: dict) -> np.ndarray:
        """
        During the triangulation process, the Triangle library
        may reorder the coordinates.
        Here, we generate a map to reorder the coordinates back
        to their original order.
        """
        logger.info ("Reordering the coordinates.")
        # Map from rows in tri['vertices'] to indices in coords
        idx_map = {tuple(row): i for i, row in enumerate(tri["vertices"])}
        
        # Generate list of indices
        return [idx_map[tuple(row)] for row in coords[:,:2]]
    
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
            ax.triplot(points[:, 0], points[:, 1], self.tri,
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
