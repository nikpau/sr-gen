# Segmental environment generator for inland waterways

## Description

This generator constructs arbitrary-looking rivers to be used as training and testing environments for simulation-based maritime applications. The generator alternates between straight and curved segments to construct the river. Several construction parameters can be changed by supplying a configuration file.

## Installation

You can install the package via

```console
$ pip install git+https://github.com/nikpau/sr-gen.git
```

## Usage

This generator can be called as a Python module from the command line for standalone use or can be part of a script.

### CLI
```console
$ rivergen -c /path/to/config.yaml
```
You can run the module with the default configuration file at `./configs/example.yaml` to see an example of the building process.

Upon running, the generator will create a folder at the specified location from the configuration. For every new generation, a new folder is created, named by a random hexadecimal UUID. This was done to avoid duplicate names when calling the generator rapidly e.g. during training. This behavior can be changed under `src/rivergen/export.py:84`.

#### Options

In case you want to test a configuration without saving it permanently to disk, consider using the `-tc` flag, which temporarily constructs a river from the given configuration and plots it for visual inspection. After closing the plot window, the constructed river is deleted.

If the visual inspection is desired but the result shall be kept, use the `-vc` flag, which keeps the files after inspection.

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
    rivergen.test.visualize(exportpath,config)


```

## Configuration files

The building behavior can be altered via several parameters to be specified inside a `yaml` configuration file. A possible configuration could look like this:

```yaml
NSEGMENTS: 10 # Total number of segements
CANAL: False # If true, the river will be a straight canal (ANGLES and RADII will be ignored)
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

# Path to the directory where the
# generated files will be saved.
# Absolute paths are recommended.
SAVEPATH: "/path/to/save/"

# Print information about the generation 
# process to stdout
VERBOSE: True
```
> The configuration file must contain all fields from the example for the generator to work.
