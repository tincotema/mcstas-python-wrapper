#!/usr/bin/env python3
# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os
from importlib import import_module
from mcpw.mcstas_wrapper import run_mcstas, run_compiler, run_instrument,\
                            valid_config, valid_mcconfig,\
                            psave, pload, load_var_list, save_var_list,\
                            check_for_detector_output, get_result_path_from_input
from os.path import isfile, isabs
import csv
#for exeption handling
class ArgumentParserError(Exception):
    pass
class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def main():
    # defining the argument parser for nice usage
    parser= ThrowingArgumentParser(description="Control command for automatic mcstas usage for the Reseda Instrument")

    subparsers = parser.add_subparsers(title="modes", required=True,
             description="Use 'manager mode --help' to view the help for any command.",
             metavar='mode')

    parser.add_argument('-p', '--python_file', dest='python_file', default='', type=str, required=True,
                       help='path (absolute or not) to the python file containing mcvariables and analyse functions')

    parser.add_argument('-d', '--result-dir', dest='result_dir', default='', type=str,
                       help='directory name for the simulationresults. If none is given or foulder name exists allrady, a increment Folder Name is generated')

    parser.add_argument('-l', '--list', dest='list', default='', type=str,
                       help='a file containing variables in csv format. first row has to match with variable names occuring in the instrument. variables that are not in here take the value from the py file. each row is a single simmulation. list will be saved together with the result for later use')

    parser_server = subparsers.add_parser('server', help='mcstas will be executed localy and the processed simulation results packed in a tarball')
    parser_server.set_defaults(func='server')

    parser_remote = subparsers.add_parser('remote', help='mcstas will be executed on a remote machine')
    parser_remote.set_defaults(func='remote')

    parser_local = subparsers.add_parser('local', help='mcstas will be executed on localy')
    parser_local.set_defaults(func='local')

    parser_full = subparsers.add_parser('full', help='mcstas will be executed on localy and the analyze function will be called after')
    parser_full.set_defaults(func='full')

    parser_analyse = subparsers.add_parser('analyse', help='analyse function will be called')
    parser_analyse.set_defaults(func='analyse')

    parser_analyse = subparsers.add_parser('custom', help='runs the mcstas compiler, c compiler and a everyting that is in the function called custom in your python file. analyse function will be called !!!EXTREMLY EXPERIMENTAL!!!')
    parser_analyse.set_defaults(func='custom')


    #retreiveng command arguments
    try:
        args = parser.parse_args()
    except ArgumentParserError as e:
        parser.print_help()
        print(f"\n{e}")
        exit(1)


    # importing var and mcvar from local_var['port']py and reseda.py files
    sys.path.append(os.getcwd())
    sys.path.append(os.path.dirname(args.python_file))
    from local_var import variables  as var
    #initializing and validating local vars
    #var = variables()
    valid_config(var)

    # adding local working directory to PATH
    sys.path.append(var['p_local'])

    # adding pyhton file location to PATH
    #importing python_file as module
    pyinstr = import_module(f"{os.path.basename(args.python_file).split('.')[0]}")
    # pulling relevant functions and classes from python file
    mcvariables = vars(pyinstr)['mcvariables']
    mcvar = vars(pyinstr)['mcvariables']
    analyse = vars(pyinstr)['analyse']
    post_simulation = vars(pyinstr)['post_simulation']
    pre_simulation = vars(pyinstr)['pre_simulation']
    # initializing mcvariables class
    #mcvar = mcvariables()
    var_list = []
    if args.list:
        if not isabs(args.list):
            if not isfile(var['p_local']/args.list):
                sys.exit(f"could not find {args.list} in {var['p_local']}")
        else:
            if not isfile(var['p_local']/args.list):
                sys.exit(f"could not find {args.list}")
        try:
            if isabs(args.list):
                var_list = load_var_list(args.list)
            else:
                var_list = load_var_list(var['p_local']/args.list)
        except Exception as e:
            sys.exit(f"could not import {args.list}. an exception occurred:\n{e}")

    msg  = ''
    #calling the correct function according to command arguments
    if 'func' not in args:
        # Fallback to --help.
        parser.print_help()
    else:
        (mcvar["sim"],msg) = get_result_path_from_input(var, mcvar, msg, args) # logic for retreiveng the correct name for the result foulder
        valid_mcconfig(var,mcvar)
        if args.func == 'analyse':
            try:
                var_list = load_var_list(var['sim_res']/mcvar["sim"]/'var_list')
            except: var_list = []
            mcvar = pload(var['sim_res']/mcvar["sim"]/'variables') #loading the correct variables
            valid_mcconfig(var,mcvar)
            check_for_detector_output(var,mcvar, var_list)
            analyse(var, mcvar, var_list)                             #call analyse, defined in reseda.py
            exit(0)
        elif args.func == 'server':#this runs the script in server mde
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            var,mcvar,var_list=pre_simulation(var,mcvar,var_list)
            run_instrument(var,mcvar, var_list)
            check_for_detector_output(var,mcvar,var_list)
            save_var_list(var_list, var['sim_res']/mcvar["sim"]/'var_list')  #save mcstas variables
            psave(mcvar, var['sim_res']/mcvar["sim"]/'variables')  #save mcstas variables
            post_simulation(var, mcvar, var_list) # contains functions that get executed after mcstas finished and can i.e. reformate the output
            sp.run(['tar', '-cf' '{}/{}.tar'.format(var['sim_res'], mcvar["sim"]), var['sim_res']/mcvar["sim"]]) #compress data

        elif args.func == 'remote':#use this if you want to run the simulation on a remote machine (setup has to be done beforhand)
            sp.run(['scp', '-r', '-P', str(var['port']), var['instr_file'], '{}:{}'.format(var['server'], var['p_server'])])#copy mcstas-instrument to remote
            sp.run(['scp', '-r', '-P', str(var['port']), 'manager.py', '{}:{}'.format(var['server'], var['p_server'])])#copy this file to remote
            sp.run(['scp', '-r', '-P', str(var['port']), 'reseda.py', '{}:{}'.format(var['server'], var['p_server'])])#copy this file to remote
            sp.run(['ssh' , '-p', str(var['port']), var['server'], 'cd {}; python {}manager.py server {}'.format(var['p_server'], var['p_server'],mcvar["sim"])])#run this file with server atribute remote
            sp.run(['scp', '-l', str(var['rate']), '-r', '-P', str(var['port']), '{}:{}.tar'.format(var['server'], var['p_server']/var['sim_res']/mcvar["sim"]), var['p_local']])#download data from remote
            sp.run(['tar', '-xf', '{}.tar'.format(mcvar["sim"])])#decompress data

        elif args.func == 'local':#use this to run the script localy
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            var,mcvar,var_list=pre_simulation(var,mcvar,var_list)
            run_instrument(var,mcvar,var_list)
            check_for_detector_output(var,mcvar,var_list)
            save_var_list(var_list, var['sim_res']/mcvar["sim"]/'var_list')  #save mcstas variables
            psave(mcvar, var['sim_res']/mcvar["sim"]/'variables')  #save mcstas variables
            post_simulation(var, mcvar,var_list) # contains functions that get executed after mcstas finished and can i.e. reformate the output

        elif args.func == 'full':
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            var,mcvar,var_list=pre_simulation(var,mcvar,var_list)
            run_instrument(var,mcvar,var_list)
            check_for_detector_output(var,mcvar,var_list)
            save_var_list(var_list, var['sim_res']/mcvar["sim"]/'var_list')  #save mcstas variables
            psave(mcvar, var['sim_res']/mcvar["sim"]/'variables')  #save mcstas variables
            post_simulation(var, mcvar, var_list) # contains functions that get executed after mcstas finished and can i.e. reformate the output
            analyse(var, mcvar,var_list)                                               #call analyse, defined in reseda.py

        elif args.func == 'custom':
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            custom = vars(pyinstr)['custom']
            custom(var,mcvar,var_list)
            analyse(var, mcvar)                                               #call analyse, defined in reseda.py
        print(msg)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"an Error occured:\n\n{e}")
