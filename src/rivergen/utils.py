import os
import sys
import yaml
import uuid
import logging
import inspect
import importlib

from pathlib import Path
from abc import ABC, abstractmethod
from typing import Generator, Tuple, Any

from . import mesh, depth, currents, config

## EXPORTER ##

# Type alias for exporter identifier
_EXPORTER_IDENTIFIER = str

class BaseExporter(ABC):
    """
    Abstract class for exporting generated data.
    
    Any implementation of this class needs to have
    at least three methods and one attribute:
    
    Methods:
    1. merge_coords()
        This method should take a mesh object and
        return a generator of coordinate points
    2. merge_metrics()
        This method should take a depth map and a
        current map and return a generator of metrics
    3. write_to_file()
        This method should take the two generators from
        above and a folder name to write the data to file.
    
    Class attribute:
    1. NAME: str
        A string representing the name of the exporter.
        This will be used by the config parser to determine
        which exporter to use.
        
    Feel free to add any implementation specific methods
    to the subclass.
    """
    NAME: _EXPORTER_IDENTIFIER
    
    def __init__(self, config: config.Configuration) -> None:
        self.config = config

    @abstractmethod
    def merge_coords(self,m: mesh.BaseSegment) -> Generator[Tuple, None, None]:
        pass

    @abstractmethod
    def merge_metrics(
        self,
        d: depth.DepthMap, 
        c: currents.CurrentMap) -> Generator[Tuple, None, None]:
        pass
    
    @abstractmethod
    def write_to_file(
        self,c_gen: Generator[Tuple, None, None],
        m_gen: Generator[Tuple, None, None],
        folder_name: Path) -> None:
        pass
    
    def export(self,*args,**kwargs) -> Any:
        """
        Exports a constructed river to a file.
        """
        parent = Path(self.config.SAVEPATH).resolve()
        
        # Check if `gen` folder exists. If not, create it.
        if not os.path.isdir(parent):
            os.mkdir(parent)

        # Create folder
        folder_name = uuid.uuid4().hex
        filepath = f"{parent}/{folder_name}"
        os.mkdir(filepath)

        # Generate data
        coords,metrics = self.construct()
        
        # Write to file
        self.write_to_file(coords,metrics,filepath)

        return filepath, coords, metrics

    def construct(self) -> Generator[Tuple, None, None]:
        """
        Main construction function. Generates xy 
        coordinates, depths and current fields
        from randomly sized curved and straight
        segments, according to the configuration
        file. 
        
        The output is generated according to the
        specified exporter in the configuration
        file.
        The folder name is a random hexadecimal 
        string.
        
        The output is saved as a whitespace separated 
        `.txt` file in a folder named by a random 
        hexadecimal string in the modules root.

        Returns:
            os.PathLike: path to folder containing 
            generated files
        """

        # Generate mesh
        builder = mesh.Builder(self.config)
        m = builder.generate()
        if self.config.VERBOSE:
            logger.info("Mesh generated.")

        # Generate depth map
        d = depth.depth_map(m,self.config)
        if self.config.VERBOSE:
            logger.info("Depth map generated.")

        # Generate current map
        c = currents.current_map(m,self.config)
        if self.config.VERBOSE:
            logger.info("Current map generated.")

        # Merge coordinates and metrics
        coords = self.merge_coords(m)
        metrics = self.merge_metrics(d,c)
        if self.config.VERBOSE:
            logger.info("Merged.")

        return coords, metrics

class ConfigFile:
    """
    Representation of a configuration file.
    
    We have to detach it from the config.py module
    to avoid circular imports, as this class is used
    to register exporters dynamically.
    """
    def __init__(self,path: str) -> None:
        args = self.load_yaml(path)
        for arg in ["LENGTHS","RADII","ANGLES"]:
            args[arg] = config.Range(**args[arg])
        self.args = args
        self.config = config.Configuration(**args)

    @staticmethod
    def load_yaml(path_to_yaml: str) -> dict[str,Any]:
        with open(path_to_yaml, "r", encoding = "utf-8") as stream:
            return yaml.safe_load(stream)

    def register_exporter(self) -> dict[str,BaseExporter]:
        # Import the module dynamically
        module_name = "rivergen.export"
        m_export = importlib.import_module(module_name)
        
        # Get all members of the module
        exporter: list[BaseExporter] = []
        for name, obj in inspect.getmembers(m_export, inspect.isclass):
            # Check if the class is defined in this module
            if obj.__module__ == module_name:
                # Check if BaseExporter is in the base classes (direct inheritance)
                for base in obj.__bases__:
                    if base.__name__ == "BaseExporter":
                        exporter.append(name)
        return self._exporter_registry(m_export,exporter)
        
    def _exporter_registry(
        self,module,
        exporter: list[str]) -> dict[str,BaseExporter]:
        """
        Helper function to create a registry of exporters.
        """
        registry = {}
        for name in exporter:
            # Get the class object
            cls = getattr(module,name)
            cls: BaseExporter
            registry[cls.NAME] = cls
        return registry

    def parse(self) -> BaseExporter:
        """
        Parses the configuration file 
        and returns its corresponding 
        exporter. 
        """
        registry = self.register_exporter()
        try:
            return registry[self.config.EXPORTER](self.config)
        except KeyError:    
            raise ValueError(
                f"No exporter named '{self.config.EXPORTER}' found. "
                "Make sure the exporter is a class inheriting from `BaseExporter` "
                "and is registered in the `export.py` module. "
                f"Currently registered exporters: {list(registry.keys())}"
            )
            
## FORMATTER ## 

# Custom formatter
# Colorize logger output if needed
color2num = dict(
    gray=30,red=31,green=32,
    yellow=33,blue=34,magenta=35,
    cyan=36,white=37,crimson=38,
)

def colorize(
    string: str, 
    color: str, 
    bold: bool = False, 
    highlight: bool = False) -> str:
    """Returns string surrounded by appropriate terminal colour codes to print colourised text.

    Args:
        string: The message to colourise
        color: Literal values are gray, red, green, yellow, blue, magenta, cyan, white, crimson
        bold: If to bold the string
        highlight: If to highlight the string

    Returns:
        Colourised string
    """
    attr = []
    num = color2num[color]
    if highlight:
        num += 10
    attr.append(str(num))
    if bold:
        attr.append("1")
    attrs = ";".join(attr)
    return f"\x1b[{attrs}m{string}\x1b[0m"

class ColoredFormatter(logging.Formatter):

    def __init__(self):
        super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style='%')

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = f'{colorize("[%(levelname)s]",color="yellow")} - %(message)s'

        elif record.levelno == logging.INFO:
            self._style._fmt = f'{colorize("[%(levelname)s]",color="green")} - %(message)s'

        elif record.levelno == logging.ERROR:
            self._style._fmt = f'{colorize("[%(levelname)s]",color="crimson",bold=True)} - %(message)s'

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result
# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = ColoredFormatter()
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)