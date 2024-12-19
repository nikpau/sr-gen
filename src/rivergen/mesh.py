"""
Mesh generating module.
This module generates straight and curved random mesh segments.
Used as a 2D river generator.
"""
import copy
import numpy as np
import random as rnd

from math import isclose
from attr import define
from collections import namedtuple
from .config import Configuration
from typing import Tuple, TypeVar, Union

TWOPI = 2*np.pi
PI = np.pi

__all__ = ["generate"]


Point = namedtuple("Point", ["x", "y"])
MeshGrid = TypeVar("MeshGrid")

@define
class Curvature:
    left: str = "left"
    right: str = "right"

@define
class BaseSegment:
    xx: np.ndarray
    yy: np.ndarray
    length: float

@define
class StraightSegment(BaseSegment):
    angle: float

    def __repr__(self):
        msg = (
            f"<StraightSegment("
            f"in_angle={'{0:.2f}'.format(rtd(self.angle))}, "
            f"length={'{0:.2f}'.format(self.length)})>"
        )
        return msg
    
@define
class CurvedSegment(StraightSegment):
    curvature: Curvature

    def __repr__(self):
        msg = (
            f"<CurvedSegment("
            f"out_angle={'{0:.2f}'.format(rtd(self.angle))}, "
            f"curvature={self.curvature}, "
            f"length={'{0:.2f}'.format(self.length)})>"
        )
        return msg

# Left/ Right endpoints of segment
# where it's connected to previous segment
@define
class RightEndpoints:
    """
    connected: Point on the "connected" end of the segment
    open     : Point on the "open" end of the segment
    """
    connected: Point
    open: Point

@define
class LeftEndpoints(RightEndpoints):
    pass
    
# Main -----------------------------------------------------
class Builder:
    def __init__(self,config: Configuration) -> None:
        self.c = config

    # Straight segment generator
    def straight_segment(self,
        start: Union[Point,CurvedSegment,StraightSegment], 
        length: float, angle: float) -> StraightSegment:
        """
        Generate a straight river segment
        with a mesh grid
        """

        if isinstance(start,(StraightSegment,CurvedSegment)):
            start = self._endpoints(start,Curvature.left).open
        
        x = np.linspace(start.x, start.x + ((self.c.GP-1)*self.c.BPD), self.c.GP)
        y = np.linspace(start.y, start.y + length, length//self.c.BPD)
        xx,yy  = np.meshgrid(x,y)

        # Positive angles rotate clockwise
        xxrot, yyrot = self._rotate(xx,yy,start,-angle)
        xxrot, yyrot = xxrot[1:,:], yyrot[1:,:] # Remove overlap

        return StraightSegment(xxrot, yyrot, length, angle)

    # Curved segment generator
    def curved_segment(self,
        prev_segment: Union[StraightSegment,CurvedSegment],
        radius:float, rot: float) -> CurvedSegment:
        """Generate curved segment

        Args:
            prev_segment (Union[StraightSegment,CurvedSegment]): Previous segment
            radius (float): Radius of the circle
            rot (float): Curvature [rad]

        Returns:
            CurvedSegment: Curved segment rotated and shifted
            to attach seamlessly to the previous segment
        """
        
        assert rot!=0,\
            "For 0 rotation use the `straight_segment` function"
        
        curvature = Curvature.right if rot > 0 else Curvature.left
        
        # Decide whether left or right endpoint should be used
        endpoints = self._endpoints(prev_segment,curvature)
        con = endpoints.connected # End connected to previous segment
        open = endpoints.open # Open end
        
        # Anchor/center point of the circle to be drawn 
        anchor = self._anchor(con,open,radius,prev_segment,curvature)
        
        # Number of equally spaced points along the circle
        n_equal_points = abs(int((radius*rot)//self.c.BPD))

        yy,xx = np.empty((self.c.GP,n_equal_points)),np.empty((self.c.GP,n_equal_points))

        for i in range(self.c.GP):
            r = radius + i*self.c.BPD
            x,y = self._evenly_spaced_points(r,n_equal_points,rot,anchor)
            xx[i,:], yy[i,:] = x,y

        # Transpose to get the circle cross-section
        # become the columns
        xx,yy = xx.T,yy.T
        
        # Rotate and flip segment such that it 
        # aligns with previous segment
        xxal,yyal = self._attach_and_align(xx,yy,anchor,prev_segment.angle,rot,curvature)
        
        xxal, yyal = xxal[1:-1,:], yyal[1:-1,:] # Remove overlap
        
        return CurvedSegment(
            xx=xxal,yy=yyal,
            angle=prev_segment.angle+rot,
            curvature=curvature,
            length=radius+((self.c.GP/2)*self.c.BPD)*rot
        )
        
    @staticmethod
    def _vertical_reflect(xx: MeshGrid, anchor: Point) -> MeshGrid:
        """
        Reflect MeshGrid about the line x = anchor.x
        """
        return 2*anchor.x - xx

    @staticmethod
    def _horizontal_reflect(yy: MeshGrid, anchor: Point) -> MeshGrid:
        """
        Reflect MeshGrid about the line y = anchor.y
        """
        return 2*anchor.y - yy

    def _attach_and_align(self,
        xx: MeshGrid, yy: MeshGrid, anchor: Point, 
        prev_angle: float, rotation: float,
        curvature: Curvature) -> Tuple[MeshGrid, MeshGrid]:
        """
        Rotate and flip a given segment such that it aligns with the previous segment
        """
        if curvature == Curvature.right:
            if prev_angle > 0: # Quadrant I & IV
                xx = self._vertical_reflect(xx,anchor)
                xx, yy = np.flip(xx,axis=1), np.flip(yy,axis=1)
                xxal, yyal = self._rotate(xx,yy,anchor,-prev_angle)
            else: # Quadrant II & III
                xx = self._vertical_reflect(xx,anchor)
                yy = self._horizontal_reflect(yy,anchor)
                xx,yy = np.flip(xx), np.flip(yy)
                xxal,yyal = self._rotate(xx,yy,anchor,-(prev_angle+rotation))
        else:
            if prev_angle > 0: # Quadrant I & IV
                xxal, yyal = self._rotate(xx,yy,anchor,-prev_angle)
            else: # Quadrant II & III
                xx = self._vertical_reflect(xx,anchor)
                yy = self._horizontal_reflect(yy,anchor)
                xxal, yyal = self._rotate(xx,yy,anchor,PI-prev_angle)

        return xxal,yyal

    def _anchor(self,
        con: Point, open: Point, radius: float, 
        prev_seg: Union[StraightSegment,CurvedSegment],
        curvature: Curvature) -> Point:
        
        x1,y1 = open.x, open.y
        x0,y0 = con.x, con.y
        s = self._anchor_switch(prev_seg.angle, curvature)
        
        # Find linear equation perpendicular to the line
        # crossing (x0,y0) and (x1,y1)
        if (x1-x0) == 0:
            x_anchor = x1+ s*radius
            y_anchor = y1
            return Point(x_anchor,y_anchor)

        m = (y1 - y0) / (x1 - x0)

        if isclose(m,0,abs_tol=1e-9): # avoid underflow 
            x_anchor = x1
            if ((prev_seg.angle > 0 and curvature == Curvature.left)
                or (prev_seg.angle < 0 and curvature == Curvature.right)):
                y_anchor = y1 + radius
            else: y_anchor = y1 - radius
            return Point(x_anchor,y_anchor)

        lineq = lambda x: -(1/m)*x+(y1+(1/m)*x1)
        
        # Find x coordinate of point with distance `radius` apart
        # from point (x1,y1) using the circle equation
        x_anchor = x1 + s*(radius/np.sqrt(1+((1/m)**2)))
        y_anchor = lineq(x_anchor)
        
        return Point(x_anchor,y_anchor)

    def _anchor_switch(self,angle: float, curvature: Curvature) -> int:
        """
        Flip sign of x_anchor calculations 
        if point in question lies in first or second quadrant
        """
        cur = 1 if curvature == Curvature.right else -1
        # Angle in quadrant I & II
        if (angle > -PI/2 and angle < PI/2):
            return 1 * cur
        else: return -1 * cur

    def _evenly_spaced_points(self,
        r: float, npoints: int, 
        curve_by: float, anchor: Point) -> list:
        """
        Generate evenly spaced points on a circle
        """
        # Angle in clockwise direction
        t = np.linspace(0, abs(curve_by), abs(npoints), endpoint=True)
        x = anchor.x + r * np.cos(t)
        y = anchor.y + r * np.sin(t)
        return x,y

    def _rotate(self,xx: MeshGrid, yy: MeshGrid, anchor: Point, rot: float) -> MeshGrid:
        """
        Rotate a MeshGrid of around an 
        anchor point by `rot` radians.
        Positive `rot` values rotate counter-clockwise
        """
        a = anchor
        xxrot = (xx-a.x)*np.cos(rot)-(yy-a.y)*np.sin(rot)+a.x
        yyrot = (xx-a.x)*np.sin(rot)+(yy-a.y)*np.cos(rot)+a.y
        return xxrot, yyrot

    def _right_endpoints(self,
        s: Union[StraightSegment,CurvedSegment]) -> RightEndpoints:
        
        connected = Point(s.xx[0][-1],s.yy[0][-1])
        open = Point(s.xx[-1][-1],s.yy[-1][-1])
        
        return RightEndpoints(connected=connected,open=open)

    def _left_endpoints(self,
        s: Union[StraightSegment,CurvedSegment]) -> LeftEndpoints:
        
        connected = Point(s.xx[0][0],s.yy[0][0])
        open = Point(s.xx[-1][0],s.yy[-1][0])
        
        return LeftEndpoints(connected=connected,open=open)

    def _endpoints(self,
        segment: Union[StraightSegment,CurvedSegment], 
        curvature: Curvature) -> Union[RightEndpoints,LeftEndpoints]:
        """
        Select endpoints depending on 
        the segments' curvature
        """
        if curvature == Curvature.right:
            return self._right_endpoints(segment)
        return self._left_endpoints(segment)

    def combine(self,
        seg1: Union[StraightSegment,CurvedSegment], 
        seg2: Union[StraightSegment,CurvedSegment]) -> BaseSegment:
        """
        Combines two segments together
        """
        
        xxcomb = np.vstack((seg1.xx, seg2.xx))
        yycomb = np.vstack((seg1.yy, seg2.yy))
        totlen = seg1.length+seg2.length
        return BaseSegment(xxcomb, yycomb, totlen)


    def _clip_to_pi(self,angle: float) -> float:
        """Clip an angle to the range [-pi,pi]"""
        return (angle+PI) % (2*PI) - PI

    def generate(self) -> BaseSegment:
        """
        Generate a sequence of random Mesh Segments
        """
        
        # Set seed for reproducibility
        if self.c.SEED  != -1:
            np.random.seed(self.c.SEED)
            rnd.seed(self.c.SEED)
        
        # First segment is always straight
        first_length = rnd.randint(*self.c.LENGTHS())
        angle = rnd.choice([-1,1])*dtr(rnd.randint(5,80))
        seg_list = []
        prev = self.straight_segment(Point(0,0), first_length, angle)

        seg_list.append(f"Segment 0: {prev!r}")
        out = copy.deepcopy(prev)

        for seg in range(self.c.NSEGMENTS-1):
            if self.c.CANAL:
                rnd_len = self.c.LENGTHS.LOW
                new = self.straight_segment(prev,rnd_len,angle)
            else: 
                rnd_len = rnd.randint(*self.c.LENGTHS())
                rnd_radius = rnd.randint(*self.c.RADII())
                rnd_angle = rnd.choice([-1,1])*dtr(rnd.randint(*self.c.ANGLES()))
                if seg%2==0: # alternate curved and straight segments
                    new = self.curved_segment(prev,rnd_radius,rnd_angle)
                    angle = self._clip_to_pi(angle + rnd_angle)
                else: new = self.straight_segment(prev,rnd_len,angle)
            
            seg_list.append(f"Segment {seg+1}: {new!r}")
            out = self.combine(out,new)
            prev = new

        return out

def rtd(angle: float) -> float:
    """Convert radians to degrees"""
    return angle*180/PI

def dtr(angle: float) -> float:
    """Convert degrees to radians"""
    return angle*PI/180
