# you schould not need to do anything in here
import sys                           #needed for executing this sript in diverent modes
import subprocess as sp              #needed to run mcstas
import argparse
import os

from mcstas_rapper import mcrun_string, psave, pload

def simulate(var, mcvar, post_mcrun_funktions, dn='', remote=False):
    msg = ''
    if not dn:
        print('no result folder name given.\n please enter one as 4th argument to this function.')
        return
    if os.path.isdir(var.p/var.p_local/var.sim_res/dn):
        print('A Simulation with this result foder name allrady exists.\n Skip Simulation.')
        return
    else:
        mcvar.dn = dn
    print(f'mcvar.dn={mcvar.dn}')
    if remote:#use this if you want to run the simulation on a remote machine (setup has to be done beforhand)
        sp.run(['scp', '-r', '-P', str(var.port), var.instr_file, '{}:{}'.format(var.server, var.p_server)])#copy mcstas-instrument to remote
        sp.run(['scp', '-r', '-P', str(var.port), 'manager.py', '{}:{}'.format(var.server, var.p_server)])#copy this file to remote
        sp.run(['scp', '-r', '-P', str(var.port), 'reseda.py', '{}:{}'.format(var.server, var.p_server)])#copy this file to remote
        sp.run(['ssh' , '-p', str(var.port), var.server, 'cd {}; python {}manager.py server {}'.format(var.p_server, var.p_server,mcvar.dn)])#run this file with server atribute remote
        sp.run(['scp', '-l', str(var.rate), '-r', '-P', str(var.port), '{}:{}.tar'.format(var.server, var.p/var.p_server/var.sim_res/mcvar.dn), var.p_local])#download data from remote
        sp.run(['tar', '-xf', '{}.tar'.format(mcvar.dn)])#decompress data
        print('remote simulation successfully\n')

    else:#use this to run the script localy
        sp.run(mcrun_string(var, mcvar), shell=True)     #run mcstas
        psave(mcvar, var.p/var.p_local/var.sim_res/mcvar.dn/'variables')  #save mcstas variables
        post_mcrun_funktions(var, mcvar, msg) # contains functions that get executed after mcstas finished and can i.e. reformate the output
        print('simulation successfully\n')
    return

def load_mcvariables(var, dn=''):
    if not dn:
        print('no result folder name given.\n please enter one as 2nd argument to this function.')
        return
    return pload(var.p/var.p_local/var.sim_res/dn/'variables') #loading the correct variables

