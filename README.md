# Segmental environment generator for inland waterways

## Description

This generator constructs arbitary looking rivers to be used as training and testing environments for simulation-based maritime applications. The generator alternates between straight and curved segments to construct the river. Several construction parameters can be changed by supplying a configuration file.

## Usage

This generator should be called as a python module from the command line like

```sh
$ python -m rivergen -c /path/to/config.yaml
```
If no config file is supplied the generator defaults to `configs/example.yaml`. The user is advised to first run the module with the default configuration to get used to the building process.

Upon running, the generator will create a `gen` folder located in the programm root. For every new generation a new folder is created, named by a random hexadecimal UUID. This was done to avoid duplicate names when calling the generator rapidly e.g. during training. This behavior can be changed under `src/rivergen/export.py:84`.

## Configuration files

The building behavior can be altered via several parameters to be specified inside a `yaml` configuation file. A possible configuration could look like this:

```yaml
NSEGMENTS: 10 # Total number of segements
GP: 76 #  No. of grid points per segment width
BPD: 20 # distance between gridpoints [m]
LENGTHS: # Range for straight segments [m] (ξ)
  LOW: 400
  HIGH: 2000
RADII: # Range of circle radii [m] (r)
  LOW: 500
  HIGH: 2000
ANGLES: # Range of angles along the circles [deg] (ϕ)
  LOW: 60
  HIGH: 80
MAX_DEPTH: 7 # River depth at deepest point [m] (κ)
MAX_VEL: 1 # Maximum current velocity [ms⁻¹] (ν)
VARIANCE: 2 # Variance for current and depth rng

# Print information about the generation 
# process to stdout
VERBOSE: True
```
> Please Note that the configuration file must contain all the fields from the example for the generator to work.
