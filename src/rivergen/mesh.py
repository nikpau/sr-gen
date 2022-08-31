"""
Mesh generating module.
This module generates straight and curved random mesh segments.
Used as a 2D river generator.
"""
import copy
import random
from collections import namedtuple
from dataclasses import dataclass
from math import isclose
from typing import Tuple, TypeVar, Union

import numpy as np

GP = 26 #  No. of grid points per segment width
BPD = 20 # distance between gridpoints [m]
BREADTH = 500 # [m] ((GP-1)*BPD)
TWOPI = 2*np.pi
PI = np.pi

__all__ = ["generate"]


Point = namedtuple("Point", ["x", "y"])
MeshGrid = TypeVar("MeshGrid")

@dataclass
class Curvature:
    left: str = "left"
    right: str = "right"

@dataclass
class BaseSegment:
    xx: np.ndarray
    yy: np.ndarray
    length: float

@dataclass
class StraightSegment(BaseSegment):
    angle: float

    def __repr__(self):
        msg = (
            f"<StraightSegment("
            f"in_angle={'{0:.2f}'.format(rtd(self.angle))}, "
            f"length={'{0:.2f}'.format(self.length)})>"
        )
        return msg
    
@dataclass
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
@dataclass
class RightEndpoints:
    """
    connected: Point on the "connected" end of the segment
    open     : Point on the "open" end of the segment
    """
    connected: Point
    open: Point

@dataclass
class LeftEndpoints(RightEndpoints):
    pass
    
# Main -----------------------------------------------------

# Straight segment generator
def straight_segment(start: Union[Point,CurvedSegment,StraightSegment], 
                     length: float, angle: float) -> StraightSegment:
    """
    Generate a straight river segment
    with a mesh grid
    """

    if isinstance(start,(StraightSegment,CurvedSegment)):
        start = _endpoints(start,Curvature.left).open
    
    x = np.linspace(start.x, start.x + BREADTH, GP)
    y = np.linspace(start.y, start.y + length, length//BPD)
    xx,yy  = np.meshgrid(x,y)

    # Positive angles rotate clockwise
    xxrot, yyrot = _rotate(xx,yy,start,-angle)
    xxrot, yyrot = xxrot[1:,:], yyrot[1:,:] # Remove overlap

    return StraightSegment(xxrot, yyrot, length, angle)

# Curved segment generator
def curved_segment(prev_segment: Union[StraightSegment,CurvedSegment],
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
    endpoints = _endpoints(prev_segment,curvature)
    con = endpoints.connected # End connected to previous segment
    open = endpoints.open # Open end
    
    # Anchor/center point of the circle to be drawn 
    anchor = _anchor(con,open,radius,prev_segment,curvature)
    
    # Number of equally spaced points along the circle
    n_equal_points = abs(int((radius*rot)//BPD))

    yy,xx = np.empty((GP,n_equal_points)),np.empty((GP,n_equal_points))

    for i in range(GP):
        r = radius + i*BPD
        x,y = _evenly_spaced_points(r,n_equal_points,rot,anchor)
        xx[i,:], yy[i,:] = x,y

    # Transpose to get the circle cross-section
    # become the columns
    xx,yy = xx.T,yy.T
    
    # Rotate and flip segment such that it 
    # aligns with previous segment
    xxal,yyal = _attach_and_align(xx,yy,anchor,prev_segment.angle,rot,curvature)
    
    xxal, yyal = xxal[1:-1,:], yyal[1:-1,:] # Remove overlap
    
    return CurvedSegment(
        xx=xxal,yy=yyal,
        angle=prev_segment.angle+rot,
        curvature=curvature,
        length=radius+((GP/2)*BPD)*rot
    )
    
def _vertical_reflect(xx: MeshGrid, anchor: Point) -> MeshGrid:
    """
    Reflect MeshGrid about the line x = anchor.x
    """
    return 2*anchor.x - xx

def _horizontal_reflect(yy: MeshGrid, anchor: Point) -> MeshGrid:
    """
    Reflect MeshGrid about the line y = anchor.y
    """
    return 2*anchor.y - yy

def _attach_and_align(
    xx: MeshGrid, yy: MeshGrid, anchor: Point, 
    prev_angle: float, rotation: float,
    curvature: Curvature) -> Tuple[MeshGrid, MeshGrid]:
    """
    Rotate and flip a given segment such that it aligns with the previous segment
    """
    if curvature == Curvature.right:
        if prev_angle > 0: # Quadrant I & IV
            xx = _vertical_reflect(xx,anchor)
            xx, yy = np.flip(xx,axis=1), np.flip(yy,axis=1)
            xxal, yyal = _rotate(xx,yy,anchor,-prev_angle)
        else: # Quadrant II & III
            xx = _vertical_reflect(xx,anchor)
            yy = _horizontal_reflect(yy,anchor)
            xx,yy = np.flip(xx), np.flip(yy)
            xxal,yyal = _rotate(xx,yy,anchor,-(prev_angle+rotation))
    else:
        if prev_angle > 0: # Quadrant I & IV
            xxal, yyal = _rotate(xx,yy,anchor,-prev_angle)
        else: # Quadrant II & III
            xx = _vertical_reflect(xx,anchor)
            yy = _horizontal_reflect(yy,anchor)
            xxal, yyal = _rotate(xx,yy,anchor,PI-prev_angle)

    return xxal,yyal

def _anchor(
    con: Point, open: Point, radius: float, 
    prev_seg: Union[StraightSegment,CurvedSegment],
    curvature: Curvature) -> Point:
    
    x1,y1 = open.x, open.y
    x0,y0 = con.x, con.y
    
    # Find linear equation perpendicular to the line
    # crossing (x0,y0) and (x1,y1)
    if (x1 - x0) == 0:
        one_over_m = np.inf
    else:
        m = (y1 - y0) / (x1 - x0)
        one_over_m = 1/m

        if isclose(m,0,abs_tol=1e-9): # avoid underflow 
            x_anchor = x1
            if ((prev_seg.angle > 0 and curvature == Curvature.left)
                or (prev_seg.angle < 0 and curvature == Curvature.right)):
                y_anchor = y1 + radius
            else:
                y_anchor = y1 - radius
            return Point(x_anchor,y_anchor)

    lineq = lambda x: -one_over_m*x+(y1+one_over_m*x1)
    
    # Find x coordinate of point with distance `radius` apart
    # from point (x1,y1) using the circle equation
    s = _anchor_switch(prev_seg.angle, curvature)
    x_anchor = x1 + s*(radius/np.sqrt(1+(one_over_m**2))) if one_over_m !=np.inf else x1
    y_anchor = lineq(x_anchor)
    
    return Point(x_anchor,y_anchor)

def _anchor_switch(angle: float, curvature: Curvature) -> int:
    """
    Flip sign of x_anchor calculations 
    if point in question lies in first or second quadrant
    """
    cur = 1 if curvature == Curvature.right else -1
    # Angle in quadrant I & II
    if (angle > -PI/2 and angle < PI/2):
        return 1 * cur
    else:
        return -1 * cur

def _evenly_spaced_points(
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

def _rotate(xx: MeshGrid, yy: MeshGrid, anchor: Point, rot: float) -> MeshGrid:
    """
    Rotate a MeshGrid of around an 
    anchor point by `rot` radians.
    Positive `rot` values rotate counter-clockwise
    """
    a = anchor
    xxrot = (xx-a.x)*np.cos(rot)-(yy-a.y)*np.sin(rot)+a.x
    yyrot = (xx-a.x)*np.sin(rot)+(yy-a.y)*np.cos(rot)+a.y
    return xxrot, yyrot

def _right_endpoints(
    s: Union[StraightSegment,CurvedSegment]) -> RightEndpoints:
    
    connected = Point(s.xx[0][-1],s.yy[0][-1])
    open = Point(s.xx[-1][-1],s.yy[-1][-1])
    
    return RightEndpoints(connected=connected,open=open)

def _left_endpoints(
    s: Union[StraightSegment,CurvedSegment]) -> LeftEndpoints:
    
    connected = Point(s.xx[0][0],s.yy[0][0])
    open = Point(s.xx[-1][0],s.yy[-1][0])
    
    return LeftEndpoints(connected=connected,open=open)

def _endpoints(
    segment: Union[StraightSegment,CurvedSegment], 
    curvature: Curvature) -> Union[RightEndpoints,LeftEndpoints]:
    """
    Select endpoints depending on 
    the segments' curvature
    """
    if curvature == Curvature.right:
        return _right_endpoints(segment)
    return _left_endpoints(segment)

def combine(
    seg1: Union[StraightSegment,CurvedSegment], 
    seg2: Union[StraightSegment,CurvedSegment]) -> BaseSegment:
    """
    Combines two segments together
    """
    
    xxcomb = np.vstack([seg1.xx, seg2.xx])
    yycomb = np.vstack([seg1.yy, seg2.yy])
    totlen = seg1.length+seg2.length
    return BaseSegment(xxcomb, yycomb, totlen)

def dtr(angle: float) -> float:
    """Convert degrees to radians"""
    return angle*PI/180

def rtd(angle: float) -> float:
    """Convert radians to degrees"""
    return angle*180/PI

def _clip_to_pi(angle: float) -> float:
    """Clip an angle to the range [-pi,pi]"""
    return (angle+PI) % (2*PI) - PI

def generate(nsegments: int, filename: str = None) -> BaseSegment:
    """
    Generate a sequence of random Mesh Segments
    """
    
    # First segment is always straight
    first_length = random.randint(400,2000)
    angle = random.choice([-1,1])*dtr(random.randint(5,80))
    seg_list = []
    prev = straight_segment(Point(0,0), first_length, angle)

    seg_list.append(f"Segment 0: {prev.__repr__()}")
    out = copy.deepcopy(prev)

    for seg in range(nsegments-1):
        rnd_len = random.randint(400,2000)
        rnd_radius = random.randint(1000,5000)
        rnd_angle = random.choice([-1,1])*dtr(random.randint(5,45))
        if seg%2==0: # alternate curved and straight segments
            new = curved_segment(prev,rnd_radius,rnd_angle)
            angle = _clip_to_pi(angle + rnd_angle)
        else:
            new = straight_segment(prev,rnd_len,angle)
        
        seg_list.append(f"Segment {seg+1}: {new.__repr__()}")
        out = combine(out,new)
        prev = new

    if filename is not None:
        np.savetxt(f"{filename}.txt",seg_list,fmt="%s")
    return out