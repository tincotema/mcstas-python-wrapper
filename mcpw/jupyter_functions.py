# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os
import re
from os.path import isdir, isfile, isabs, islink
from mcpw.setup_tools import create_local_var, create_mcvar_dict
from mcpw.mcstas_wrapper import run_mcstas, run_compiler,\
                                run_instrument, is_scan,\
                                check_for_detector_output,\
                                psave, pload, which, valid_config,\
                                save_var_list, scan
from mcpw.mcstas_wrapper import load_var_list as mcpw_load_var_list
def load_mcvariables(var, sim=''): # loads used parameters from simulation
    if not sim:
        print('no result folder name given.\n please enter one as 2nd argument to this function.')
        return
    mcvar =  pload(var['sim_res']/sim/'variables') #loading the correct variables
    print(f'available parameters in mcvariables: {", ".join(list(mcvar.keys()))}')
    return mcvar

def load_var_list(var,mcvar):
    try:
        return mcpw_load_var_list(var['sim_res']/mcvar['sim']/'var_list')
    except:
        return []

def simulate(var, mcvar, var_list=[], var_list_csv='', sim='', remote=False): #spawns a simulation if sim dose not jet exists and returns a list of result dirs
    msg = ''
    #checking for imput
    if not sim:
        print('no result folder name given.\n please enter one as 4th argument to this function.')
        return

    # checking if the result folder exists and if yes, load mcvariables and create output list
    if os.path.isdir(var['sim_res']/sim):
        print('A Simulation with this result foder name allrady exists, skip Simulation.\n')
        res_list = []
        if is_scan(mcvar):
            for i in range(scan(mcvar).N):
                res_list.append(var['sim_res']/mcvar['sim']/str(i))
        else:
            res_list.append(var['sim_res']/mcvar['sim'])
        return load_mcvariables(var, sim), res_list
    else:
        mcvar['sim'] = sim

    # check if var_list or var_list file is given.
    if var_list_csv and not var_list:
        if not isabs(var_list_csv):
            if not isfile(var['p_local']/var_list_csv):
                sys.exit(f"could not find {var_list_csv} in {var['p_local']}")
        else:
            if not isfile(var['p_local']/var_list_csv):
                sys.exit(f"could not find {var_list_csv}")
        try:
            if isabs(var_list_csv):
                var_list = mcpw_load_var_list(var_list_csv)
            else:
                var_list = mcpw_load_var_list(var['p_local']/var_list_csv)
        except Exception as e:
            sys.exit(f"could not import {var_list_csv}. an exception occurred:\n{e}")

    # if remote simulation is True (setup has to be done beforhand)
    if remote:
        sp.run(['scp', '-r', '-P', str(var['port']), var.instr_file, '{}:{}'.format(var['server'], var['p_server'])])#copy mcstas-instrument to remote
        sp.run(['scp', '-r', '-P', str(var['port']), 'manager.py', '{}:{}'.format(var['server'], var['p_server'])])#copy this file to remote
        sp.run(['scp', '-r', '-P', str(var['port']), 'reseda.py', '{}:{}'.format(var['server'], var['p_server'])])#copy this file to remote
        sp.run(['ssh' , '-p', str(var['port']), var['server'], 'cd {}; python {}manager.py server {}'.format(var['p_server'], var['p_server'],mcvar['sim'])])#run this file with server atribute remote
        sp.run(['scp', '-l', str(var['rate']), '-r', '-P', str(var['port']), '{}:{}.tar'.format(var['server'], var.p/var['p_server']/var['sim_res']/mcvar['sim']), var['p_local']])#download data from remote
        sp.run(['tar', '-xf', '{}.tar'.format(mcvar['sim'])])#decompress data
        print('remote simulation successfully\n')
        res_list = []
        if is_scan(mcvar):
            for i in range(scan(mcvar).N):
                res_list.append(var['sim_res']/mcvar['sim']/str(i))
        else:
            res_list.append(var['sim_res']/mcvar['sim'])
        return mcvar, res_list

    # run the script localy
    else:
        run_mcstas(var,mcvar)
        run_compiler(var,mcvar)
        res = run_instrument(var,mcvar, var_list)
        check_for_detector_output(var,mcvar, var_list)
        save_var_list(var_list, var['sim_res']/mcvar['sim']/'var_list')  #save mcstas variables
        psave(mcvar, var['sim_res']/mcvar['sim']/'variables')  #save mcstas variables
        print('simulation successfully\n')
        return mcvar, res

# helper function
def print_mcvariable_from_instrument(instrument):
    for line in create_class_mcvariables_lines(instrument):
        print(line)

# fuction to create local_var.py and load it
def initialize(instrument='', working_dir=os.getcwd(), mcstas='mcstas', output_dir='simulation_results', component_dir='', mpi=0):
    # substituting \ for / to avoid complications with the paths
    if os.name == 'nt':
        working_dir   = re.sub(r'\\','/', working_dir)
        mcstas        = re.sub(r'\\','/', mcstas)
        instrument    = re.sub(r'\\','/', instrument)
        output_dir    = re.sub(r'\\','/', output_dir)
        component_dir = re.sub(r'\\','/', component_dir)

    # checking instrument file
    instr_file = working_dir + "/" + instrument
    if not isfile(instr_file):
        sys.exit(f" the instrument file '{instrument}' is not located in the working directory '{working_dir}'")
    if not instrument.split('.')[1] == "instr":
        sys.exit(f"the given instrument file has not the correct ending:\
                 \nexpected: {instrument.split('.')[0]}.instr\
                 \ngot: {instrument}\
                 \nplease make shure to give a valid instrument file")

    # checking working directory
    if not isdir(working_dir):
        sys.exit(f"the given working directory '{working_dir}' dose not exist")

    # checking output directory
    if isabs(output_dir):
        if not isdir(output_dir):
            sys.exit(f"the given simulation result directory '{output_dir}' dose not exist")
    else:
        if not isdir(f"{working_dir}/{output_dir}"):
            os.mkdir(f"{working_dir}/{output_dir}")
            print(f"created simulation result directory '{output_dir}' in the working directory")

    # checking for mcstas executable
    mcstas_exe = which(mcstas)
    if not mcstas_exe:
        print(f"\nMcStas is not installed or the Path is inocrrect: {mcstas}")
        return
    if islink(mcstas_exe):
        mcstas = os.readlink(mcstas_exe)
    else:
        mcstas = mcstas_exe

    # checking gcc or mpi existence
    if mpi == 0:
        # test if gcc exists
        if os.name=='nt':
            which("gcc --help")
        else:
            which("gcc")
    else:
        # test if mpicc exists
        if os.name=='nt':
            pass
        else:
            which("mpicc")

    # parsing arguments
    args= argparse.Namespace(working_dir=working_dir,\
                            mcstas=mcstas,\
                            instrument=instrument,\
                            output_dir=output_dir,\
                            component_dir=component_dir,\
                            mpi = mpi)

    # creating local_var.py file if not exiisting
    #TODO: check if imput correspont to existing local_var.py and give user feedback
    if not os.path.isfile(f"{working_dir}/local_var.py"):
        create_local_var(args)
    # importing local variables
    sys.path.append(working_dir)
    from local_var import variables
    var = variables()
    valid_config(var)
    print("usefull variables: var['sim_res'] directory where simulation_results are saved.\n\
                        in combination with mcvar['sim'] you get the full path to your detector files:\n\
                        var['sim_res']/mcvar['sim'] \n\
                        if you run a scan append /str(n) for n_th step\n\
                   var['p_local'] working directory\n")
    # printing mcvariables class
    print(f'####################\ncopy the following part and execute it in a new cell\n####################\n')
    print("from mcpw.mcstas_wrapper import Scan\n")
    for line in create_mcvar_dict(instr_file):
        print(line)
    print("\n#for laziness:")
    print("mcvar = mcvariables\n")
    print(f'####################\nend of cell\n####################')

    return var
