import triangle as tr
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
import matplotlib.tri as mtri

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
                
class UCDExporter(BaseExporter):
    """
    Exporter class to write the generated
    data as an AVS-UCD (Unstructured Cell Data) file.
    """
    NAME = "ucd"
    def __init__(self,config: config.Configuration) -> None:
        super().__init__(config)
    
    def merge_coords(self,m: mesh.BaseSegment) -> np.ndarray:
        """Decompose mesh grid to 1d arrays of coordinates.
        We output a 2D array with x and y coordinates instead
        of a generator as we need these values two times:
        1. For the coordinates file
        2. For the mesh triangulation
        """
        mx = np.hstack(m.xx)
        my = np.hstack(m.yy)
        mz = np.zeros_like(mx)
        index = np.arange(1,len(mx)+1)
        mx: np.ndarray; my: np.ndarray
        
        assert mx.shape == my.shape == mz.shape
        
        return np.array([index,mx,my,mz]).T
    
    def _header(self) -> str:
        msg1 = (
            "# AVS-UCD FILE CREATED BY "
            "SEG-GEN "
            f"at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        return msg1
    
    def _define_mesh(self, tri: Delaunay, coords: np.ndarray) -> str:
        return f"{coords.shape[0]} {tri["triangles"].shape[0]} 3 0 0\n"
    
    def _variable_definition(self) -> str:
        return "2 2 1\nUV,m/s\nS,mNN\n"
    
    def merge_metrics(
        self,depth: depth.DepthMap,
        currents: currents.CurrentMap) -> Generator[Tuple, None, None]:
        """
        Merge depth map and current map into a generator for further processing.
        """
        depth = np.hstack(depth)
        cx = np.hstack(currents.x)
        cy = np.hstack(currents.y)
        index = np.arange(1,len(depth)+1)
        
        l = [index,depth,cx,cy]
    
        if not all(map(lambda x: x.shape == l[0].shape,l)):
            raise ValueError("Shapes of depth map and current maps do not match.")  
        
        return zip(index,cy,cx,depth)

    def triangulate_coords(self, data: np.ndarray) -> Delaunay:
        """
        Delaunay triangulation of the coordinates, to generate
        the mesh for the UCD file.
        """
        # The coordinates are in the second and third column,
        # as they come from the merge_coords method ->[index,x,y,z]
        coords = data[:,1:3]
        return Delaunay(coords)
    
    def river_polygon(self, coords: np.ndarray) -> Polygon:
        """
        Create a polygon from the coordinates of the river.
        """
        # The shell of the polygon consists of the first and
        # last cross section of the river as well as the border
        # points of each other cross section.
        xy = coords[:,1:3]
        
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
        return Polygon(boundary)
    
    def _CDT(self,coords: np.ndarray) -> dict:
        """
        Perform Constrained Delaunay Triangulation 
        using the Triangle library.
        """
        bounds = self.river_polygon(coords)
        bounds = bounds[:-1] # Remove the last point to close the polygon
        segments = [(i, (i + 1) % len(bounds)) for i in range(len(bounds))]
        
        # Prepare data for triangulation
        xy = coords[:,1:3]
        
        # Revome all boundary points from the coordinates
        xy = xy[~np.isin(xy,bounds).all(axis=1)]
        
        combined = np.vstack((bounds,xy))
        data = dict(vertices=combined,segments=segments)
        
        # Perform the triangulation
        tri = tr.triangulate(data, 'p')
        
        return tri
        
    def spatial_mask(
        self,coords: np.ndarray, 
        tri: Delaunay, poly: Polygon) -> np.ndarray:
        """
        
        """
        # Prepare data for matplotlib triangulation
        xy = coords[:,1:3]
        triang = mtri.Triangulation(xy[:, 0], xy[:, 1], tri.simplices)

        # Mask triangles outside the river
        mask = []
        for simplex in tri.simplices:
            triangle = xy[simplex]
            centroid = np.mean(triangle, axis=0)
            if poly.contains(Point(centroid)):
                mask.append(False)
            else:
                mask.append(True)

        triang.set_mask(mask)
        
        return triang
    
    def write_to_file(
        self, 
        coords: np.ndarray,
        m_gen: Generator[Tuple, None, None],
        folder_name: Path) -> None:
        """Write to file."""
        
        # Perform Constrained Delaunay Triangulation
        self.tri = self._CDT(coords)
        # Prepare data for the UCD file
        tri_indices = np.arange(1, self.tri["triangles"].shape[0] + 1)
        meshdef = self._define_mesh(self.tri, coords)

        with open(f"{folder_name}/rnd_rvr.inp", "w") as f:
            f.write(self._header())

            # Prepare and write node data
            node_lines = [f"{int(row[0])} {row[1]} {row[2]} {row[3]}\n" for row in coords]
            f.writelines(node_lines)

            # Write the mesh definition
            f.write(meshdef)

            # Prepare and write mesh data
            mesh_lines = [
                f"{int(idx)} {int(idx)} tri {row[0]} {row[1]} {row[2]}\n"
                for idx, row in zip(tri_indices, self.tri["triangles"])
            ]
            f.writelines(mesh_lines)

            # Write the variable definition
            f.write(self._variable_definition())

            # Prepare and write metric data
            metric_lines = [
                f"{int(row[0])} {row[1]} {row[2]} {row[3]}\n"
                for row in m_gen
            ]
            f.writelines(metric_lines)
                
    def plot_triangulation(
        self, show_points=True, show_triangles=True, 
        point_labels=False, point_color='red', 
        line_color='blue', point_size=5, line_width=0.5):
        """
        Plot Delaunay triangulation with additional features.
        """
        # Compute Delaunay triangulation if not provided
        triangulation = self.tri
        points = triangulation["vertices"]
        
        # Create a matplotlib figure and axes
        fig, ax = plt.subplots(figsize=(8, 6))
        ax: plt.Axes
        
        if show_triangles:
            # Plot the triangulation edges
            ax.triplot(points[:, 0], points[:, 1], self.tri["triangles"],
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
