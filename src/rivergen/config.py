from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional


class Range(BaseModel):
    LOW: int
    HIGH: int

    def __call__(self) -> tuple[int, int]:
        return (self.LOW, self.HIGH)


class Configuration(BaseModel):
    SEED: int          # Seed for the random number generator
    NSEGMENTS: int     # Total number of segements
    MODE: Literal["river", "canal", "plane"] = Field(default="river")  # Generation mode
    GP: int            # No. of grid points per segment width
    BPD: int           # distance between gridpoints [m]
    EDGELEN: int = Field(default=1000)  # Length of plane edges [m] (ignored for river and canal)
    LENGTHS: Range     # Range for straight segments [m] (ξ) (ignored in plane mode)
    RADII: Range       # Range of circle radii [m] (r) (ignored in plane mode)
    ANGLES: Range      # Range of angles along the circles [deg] (ϕ) (ignored in plane mode)
    MAX_DEPTH: int     # River depth at deepest point [m] (κ)
    MAX_VEL: int       # Maximum current velocity [ms⁻¹] (ν)
    VARIANCE: int      # Variance for current and depth rng
    START_AT_UTM: int  # UTM zone to start the river at
    VERBOSE: bool = Field(default=False)      # Print process information about the generation 
    SAVEPATH: str      # Path to save the generated river
    EXPORTER: str = Field(default="csv")      # Exporter to use (e.g. "csv")
    
    # For backward compatibility with YAML files that use CANAL field
    CANAL: Optional[bool] = Field(default=None, exclude=True)

    @model_validator(mode='before')
    @classmethod
    def handle_canal_field(cls, values):
        """Convert CANAL boolean field to MODE string for backward compatibility"""
        if isinstance(values, dict):
            canal = values.get('CANAL')
            if canal is not None and 'MODE' not in values:
                values['MODE'] = 'canal' if canal else 'river'
            # Remove CANAL from values since it's excluded
            values.pop('CANAL', None)
        return values

    @field_validator('SEED')
    @classmethod
    def validate_seed(cls, v):
        """Ensure seed is valid"""
        if v < -1:
            raise ValueError('SEED must be -1 or a positive integer')
        return v

