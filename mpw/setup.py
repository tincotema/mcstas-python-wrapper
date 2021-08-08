#!/usr/bin/env python3
# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os
from setup_tools import create_local_var, create_python_file




#for exeption handling
class ArgumentParserError(Exception):
    pass
class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)



# defining the argument parser for nice usage
parser= ThrowingArgumentParser(description="Script to create a python file to control a McStas Instrument with MPW")

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
                    help='additional directory where mcstas will search for components; default=""')

#parser_analyse = subparsers.add_parser('analyse', help='analyse function will be called')
#parser_analyse.set_defaults(func='analyse')



#retreiveng command arguments
try:
    args = parser.parse_args()
except ArgumentParserError as e:
    print(e)
    exit(1)

if not os.path.isfile(f"{args.working_dir}/local_var.py"):
    create_local_var(args)
else:
    print(f"local_var.py allready exists")

if not os.path.isfile(f"{args.working_dir}/{args.instrument.split('.')[0]}.py"):
    create_python_file(args)
else:
    print(f"{args.instrument.split('.')[0]}.py allready exists")







#msg  = ''
##calling the correct function according to command arguments
#if 'func' not in args:
#    # Fallback to --help.
#    parser.print_help()
#else:
#    (mcvar.dn,msg) = get_result_path_from_input(var, mcvar, msg, args) # logic for retreiveng the correct name for the result foulder
#    if args.func == 'analyse':
#        mcvar = pload(var.p/var.p_local/var.sim_res/mcvar.dn/'variables') #loading the correct variables
#        analyse(var, mcvar, msg)                                               #call analyse, defined in reseda.py
#        exit(0)
#
#    elif args.func == 'full':
#        sp.run(mcrun_string(var, mcvar), shell=True)     #run mcstas
#        psave(mcvar, var.p/var.p_local/var.sim_res/mcvar.dn/'variables')  #save mcstas variables
#        post_mcrun_funktions(var, mcvar, msg) # contains functions that get executed after mcstas finished and can i.e. reformate the output
#        analyse(var, mcvar, msg)                                               #call analyse, defined in reseda.py
#    print(msg)
