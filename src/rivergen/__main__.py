from rivergen import export
from argparse import ArgumentParser
from rivergen.config import ConfigFile
from rivergen.tests import rivergen_test

parser = ArgumentParser()

parser.add_argument(
    "-c","--config",type=str,default="./configs/example.yaml",
    help="File path to your configuration file.\nDefaults to './configs/example.yaml'"
)
parser.add_argument(
    "-t", "--test", action="store_true"
)

args = parser.parse_args()

if not args.test:
    CONFIG = ConfigFile(args.config).export()
    export.export_to_file(CONFIG)
else:
    rivergen_test(args.config)