# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os
import re
from os.path import isdir, isfile, isabs
from mcpw.setup_tools import create_local_var, create_class_mcvariables_lines
from mcpw.mcstas_wrapper import run_mcstas, run_compiler,\
                                run_instrument, is_scan,\
                                check_for_detector_output,\
                                psave, pload, which, valid_config

def simulate(var, mcvar, dn='', remote=False): #spawns a simulation if dn dose not jet exists and returns a list of result dirs
    msg = ''
    if not dn:
        print('no result folder name given.\n please enter one as 4th argument to this function.')
        return
    if os.path.isdir(var.sim_res/dn):
        print('A Simulation with this result foder name allrady exists.\n Skip Simulation.')
        return
    else:
        mcvar.dn = dn
    #print(f'mcvar.dn={mcvar.dn}')
    if remote:#use this if you want to run the simulation on a remote machine (setup has to be done beforhand)
        sp.run(['scp', '-r', '-P', str(var.port), var.instr_file, '{}:{}'.format(var.server, var.p_server)])#copy mcstas-instrument to remote
        sp.run(['scp', '-r', '-P', str(var.port), 'manager.py', '{}:{}'.format(var.server, var.p_server)])#copy this file to remote
        sp.run(['scp', '-r', '-P', str(var.port), 'reseda.py', '{}:{}'.format(var.server, var.p_server)])#copy this file to remote
        sp.run(['ssh' , '-p', str(var.port), var.server, 'cd {}; python {}manager.py server {}'.format(var.p_server, var.p_server,mcvar.dn)])#run this file with server atribute remote
        sp.run(['scp', '-l', str(var.rate), '-r', '-P', str(var.port), '{}:{}.tar'.format(var.server, var.p/var.p_server/var.sim_res/mcvar.dn), var.p_local])#download data from remote
        sp.run(['tar', '-xf', '{}.tar'.format(mcvar.dn)])#decompress data
        print('remote simulation successfully\n')
        res_list = []
        if is_scan(mcvar):
            for i in range(mcvar.scan.N):
                res_list.append(var.sim_res/mcvar.dn/str(i))
        else:
            res_list.append(var.sim_res/mcvar.dn)
        return res_list

    else:#use this to run the script localy
        run_mcstas(var,mcvar)
        run_compiler(var,mcvar)
        res = run_instrument(var,mcvar)
        check_for_detector_output(var,mcvar)
        psave(mcvar, var.sim_res/mcvar.dn/'variables')  #save mcstas variables
        #post_mcrun_funktions(var, mcvar, msg) # contains functions that get executed after mcstas finished and can i.e. reformate the output
        print('simulation successfully\n')

        return res

def print_mcvariable_from_instrument(instrument):
    for line in create_class_mcvariables_lines(instrument):
        print(line)

def load_mcvariables(var, dn=''): # loads used parameters from simulation
    if not dn:
        print('no result folder name given.\n please enter one as 2nd argument to this function.')
        return
    return pload(var.sim_res/dn/'variables') #loading the correct variables

def initialize(instrument='', working_dir=os.getcwd(), mcstas='mcstas', output_dir='simulation_results', component_dir='', mpi=0):
    if os.name == 'nt':
        working_dir   = re.sub(r'\\','/', working_dir)
        mcstas        = re.sub(r'\\','/', mcstas)
        instrument    = re.sub(r'\\','/', instrument)
        output_dir    = re.sub(r'\\','/', output_dir)
        component_dir = re.sub(r'\\','/', component_dir)

    instr_file = working_dir + "/" + instrument
    if not isfile(instr_file):
        sys.exit(f" the instrument file '{instrument}' is not located in the working directory '{working_dir}'")
    if not instrument.split('.')[1] == "instr":
        sys.exit(f"the given instrument file has not the correct ending:\
                 \nexpected: {instrument.split('.')[0]}.instr\
                 \ngot: {instrument}\
                 \nplease make shure to give a valid instrument file")

    if not isdir(working_dir):
        sys.exit(f"the given working directory '{working_dir}' dose not exist")
    if isabs(output_dir):
        if not isdir(output_dir):
            sys.exit(f"the given simulation result directory '{output_dir}' dose not exist")
    else:
        if not isdir(f"{working_dir}/{output_dir}"):
            os.mkdir(f"{working_dir}/{output_dir}")
            print(f"created simulation result directory '{output_dir}' in the working directory")

    if os.name=='nt':
        which(f"{mcstas} -v")
    else:
        which(mcstas)
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

    args= argparse.Namespace(working_dir=working_dir,\
                            mcstas=mcstas,\
                            instrument=instrument,\
                            output_dir=output_dir,\
                            component_dir=component_dir,\
                            mpi = mpi)

    if not os.path.isfile(f"{working_dir}/local_var.py"):
        create_local_var(args)

    sys.path.append(working_dir)
    from local_var import variables
    var = variables()
    valid_config(var)

    print(f'####################\ncopy the following part and execute it in a new cell\n####################\n')
    print("from mcpw.mcstas_wrapper import Scan\n")
    for line in create_class_mcvariables_lines(instr_file):
        print(line)
    print("mcvar = mcvariables()\n")
    print(f'####################\nend of cell\n####################')

    return var
