from attr import define

@define(frozen=True)
class Range:
    LOW: float
    HIGH: float

    def __call__(self) -> tuple[float,float]:
        return tuple([self.LOW,self.HIGH])

@define(frozen=True)
class Configuration:
    SEED: int       # Seed for the random number generator
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
    EXPORTER: str   # Exporter to use (e.g. "csv")

