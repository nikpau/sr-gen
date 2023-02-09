from rivergen import export
from argparse import ArgumentParser
from rivergen.config import ConfigFile

parser = ArgumentParser()

parser.add_argument(
    "-c","--config",type=str,default="./configs/example.yaml",
    help="File path to your configuration file.\nDefaults to './configs/example.yaml'"
)
args = parser.parse_args()

CONFIG = ConfigFile(args.config).export()
export.export_to_file(CONFIG)