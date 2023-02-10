# Segmental environment generator for inland waterways

## Description

This generator constructs arbitrary-looking rivers to be used as training and testing environments for simulation-based maritime applications. The generator alternates between straight and curved segments to construct the river. Several construction parameters can be changed by supplying a configuration file.

## Installation

You can install the package via

```console
$ pip install git+https://github.com/nikpau/sr-gen.git
```

## Usage

This generator can be called as a python module from the command line for standalone use or can be part of a script.

### CLI
```console
$ python -m rivergen -c /path/to/config.yaml
```
The user is advised to first run the module with the default configuration `./configs/example.yaml` to get used to the building process.

Upon running, the generator will create a `gen` folder located in the program root. For every new generation, a new folder is created, named by a random hexadecimal UUID. This was done to avoid duplicate names when calling the generator rapidly e.g. during training. This behavior can be changed under `src/rivergen/export.py:84`.

#### Options

In case you want to test a configuration without saving it permanently to disk, consider using the `-tc` flag, which temporarily constructs a river from the given configuration and plots it for visual inspection. After closing the plot window, the constructed river is deleted.

If the visual inspection is desired but the result shall be kept, use the `-vc` flag, which skips the deletion of the river after inspection.

### Script

The generator can be included in any script by first registering a configuration and then exporting rivers generated from it to a file. For example:

```python
import rivergen

# Register configuration file
config = rivergen.ConfigFile("/path/to/config.yaml").export()

# Generate 10 random rivers from this configuration
# and plot them for inspection
for _ in range(10):
    exportpath = rivergen.export_to_file(config)
    rivergen.test.visulaize(exportpath,config)


```

## Configuration files

The building behavior can be altered via several parameters to be specified inside a `yaml` configuration file. A possible configuration could look like this:

```yaml
NSEGMENTS: 10 # Total number of segements
GP: 50 #  No. of grid points per segment width
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