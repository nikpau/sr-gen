from typing import Any
import yaml
from dataclasses import dataclass

@dataclass(frozen=True)
class Range:
    LOW: float
    HIGH: float

    def __call__(self) -> tuple[float,float]:
        return tuple([self.LOW,self.HIGH])

@dataclass(frozen=True)
class Configuration:
    NSEGMENTS: int  # Total number of segements
    CANAL: bool     # Generate a straight canal (RADII and ANGLES are ignored)
    GP: int         # No. of grid points per segment width
    BPD: int        # distance between gridpoints [m]
    LENGTHS: Range  # Range for straight segments [m] (ξ)
    RADII: Range    # Range of circle radii [m] (r)
    ANGLES: Range   # Range of angles along the circles [deg] (ϕ)
    MAX_DEPTH: int  # River depth at deepest point [m] (κ)
    MAX_VEL: int    # Maximum current velocity [ms⁻¹] (ν)
    VARIANCE: int   # Variance for current and depth rng
    VERBOSE: bool   # Print process information about the generation 
    SAVEPATH: str   # Path to save the generated river

class ConfigFile:
    def __init__(self,path: str) -> None:
        args = self._parse(path)
        _ranges = ["LENGTHS","RADII","ANGLES"]
        for keyword in _ranges:
            args[keyword] = Range(**args[keyword])
        self.args = args

    @staticmethod
    def _parse(path_to_yaml: str) -> dict[str,Any]:
        with open(path_to_yaml, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError:
                raise

    def export(self):
        """Exports a ConfigFile object
        to a configuration dataclass"""
        return Configuration(**self.args)