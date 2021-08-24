#!/usr/bin/env python3
# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os
import re
from mcpw.setup_tools import create_local_var, create_python_file




#for exeption handling
class ArgumentParserError(Exception):
    pass
class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def main():
    # defining the argument parser for nice usage
    parser= ThrowingArgumentParser(description="Script to create a python file to control a McStas Instrument with MCPW")

    subparsers = parser.add_subparsers(title="modes",
             description="Use 'manager mode --help' to view the help for any command.",
             metavar='mode')

    parser.add_argument('-I', '--instrument', dest='instrument', default='', type=str, required=True,
                        help='mcstas instrument you want to control with mpw')
    parser.add_argument('-d', '--working_dir', dest='working_dir', default=os.getcwd(), type=str,
                        help='path to working directory (optional)')
    parser.add_argument('-m', '--mcstas', dest='mcstas', default='mcstas', type=str,
                        help='path to mcstas executable; default=mcstas')
    parser.add_argument('-o', '--output_dir', dest='output_dir', default='simulation_results', type=str,
                        help='name in the simulation results directory; default=simulation_results')
    parser.add_argument('-c', '--component_dir', dest='component_dir', default='', type=str,
                        help='additional directory where mcstas will search for components needs to be a absolute path; default=""')
    parser.add_argument('-M', '--MPI', dest='mpi', default=0, type=int,
                        help='additional directory where mcstas will search for components needs to be a absolute path; default=""')


    #retreiveng command arguments
    try:
        args = parser.parse_args()
    except ArgumentParserError as e:
        print(e)
        exit(1)

    if os.name == 'nt':
        args.working_dir   = re.sub(r'\\','/', args.working_dir)
        args.mcstas        = re.sub(r'\\','/', args.mcstas)
        args.instrument    = re.sub(r'\\','/', args.instrument)
        args.output_dir    = re.sub(r'\\','/', args.output_dir)
        args.component_dir = re.sub(r'\\','/', args.component_dir)


    if not os.path.isfile(f"{args.working_dir}/local_var.py"):
        create_local_var(args)
    else:
        print(f"local_var.py allready exists")

    if not os.path.isfile(f"{args.working_dir}/{args.instrument.split('.')[0]}.py"):
        create_python_file(args)
    else:
        print(f"{args.instrument.split('.')[0]}.py allready exists")


if __name__ == '__main__':
    main()


