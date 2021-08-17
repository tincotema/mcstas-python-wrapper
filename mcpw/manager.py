#!/usr/bin/env python3
# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os
from importlib import import_module
from mcpw.mcstas_wrapper import run_mcstas, run_compiler, run_instrument,\
                            valid_config, valid_mcconfig,\
                            psave, pload,\
                            check_for_detector_output, get_result_path_from_input

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



    #retreiveng command arguments
    try:
        args = parser.parse_args()
    except ArgumentParserError as e:
        parser.print_help()
        print(f"\n{e}")
        exit(1)


    # importing var and mcvar from local_var.py and reseda.py files
    sys.path.append(os.getcwd())
    sys.path.append(os.path.dirname(args.python_file))
    from local_var import variables

    var = variables()
    valid_config(var)


    # adding local working directory to PATH
    sys.path.append(var.p_local)
    # adding pyhton file location to PATH
    #importing python_file as module
    pyinstr = import_module(f"{os.path.basename(args.python_file).split('.')[0]}")

    # pulling relevant functions and classes from python file
    mcvariables = vars(pyinstr)['mcvariables']
    analyse = vars(pyinstr)['analyse']
    post_mcrun_funktions = vars(pyinstr)['post_mcrun_funktions']
    # initializing mcvariables class
    mcvar = mcvariables()

    msg  = ''
    #calling the correct function according to command arguments
    if 'func' not in args:
        # Fallback to --help.
        parser.print_help()
    else:
        (mcvar.dn,msg) = get_result_path_from_input(var, mcvar, msg, args) # logic for retreiveng the correct name for the result foulder
        valid_mcconfig(var,mcvar)
        if args.func == 'analyse':
            mcvar = pload(var.sim_res/mcvar.dn/'variables') #loading the correct variables
            valid_mcconfig(var,mcvar)
            check_for_detector_output(var,mcvar)
            analyse(var, mcvar, msg)                                               #call analyse, defined in reseda.py
            exit(0)
        if args.func == 'server':#this runs the script in server mde
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            run_instrument(var,mcvar)
            check_for_detector_output(var,mcvar)
            psave(mcvar, var.sim_res/mcvar.dn/'variables')  #save mcstas variables
            post_mcrun_funktions(var, mcvar, msg) # contains functions that get executed after mcstas finished and can i.e. reformate the output
            sp.run(['tar', '-cf' '{}/{}.tar'.format(var.sim_res, mcvar.dn), var.sim_res/mcvar.dn]) #compress data

        elif args.func == 'remote':#use this if you want to run the simulation on a remote machine (setup has to be done beforhand)
            sp.run(['scp', '-r', '-P', str(var.port), var.instr_file, '{}:{}'.format(var.server, var.p_server)])#copy mcstas-instrument to remote
            sp.run(['scp', '-r', '-P', str(var.port), 'manager.py', '{}:{}'.format(var.server, var.p_server)])#copy this file to remote
            sp.run(['scp', '-r', '-P', str(var.port), 'reseda.py', '{}:{}'.format(var.server, var.p_server)])#copy this file to remote
            sp.run(['ssh' , '-p', str(var.port), var.server, 'cd {}; python {}manager.py server {}'.format(var.p_server, var.p_server,mcvar.dn)])#run this file with server atribute remote
            sp.run(['scp', '-l', str(var.rate), '-r', '-P', str(var.port), '{}:{}.tar'.format(var.server, var.p_server/var.sim_res/mcvar.dn), var.p_local])#download data from remote
            sp.run(['tar', '-xf', '{}.tar'.format(mcvar.dn)])#decompress data

        elif args.func == 'local':#use this to run the script localy
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            run_instrument(var,mcvar)
            check_for_detector_output(var,mcvar)
            psave(mcvar, var.sim_res/mcvar.dn/'variables')  #save mcstas variables
            post_mcrun_funktions(var, mcvar, msg) # contains functions that get executed after mcstas finished and can i.e. reformate the output

        elif args.func == 'full':
            run_mcstas(var,mcvar)
            run_compiler(var,mcvar)
            run_instrument(var,mcvar)
            check_for_detector_output(var,mcvar)
            psave(mcvar, var.sim_res/mcvar.dn/'variables')  #save mcstas variables
            post_mcrun_funktions(var, mcvar, msg) # contains functions that get executed after mcstas finished and can i.e. reformate the output
            analyse(var, mcvar, msg)                                               #call analyse, defined in reseda.py
        print(msg)

if __name__ == '__main__':
    main()
