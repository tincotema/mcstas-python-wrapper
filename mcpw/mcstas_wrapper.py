import numpy as np                   #needed for the arrays
import subprocess as sp              #needed to run mcstas
import sys                           #needed to select program mode of this script
import pickle                        #needed to save mcstas variables for later use
import os
from os.path import isfile, isdir, isabs, dirname, basename, splitext, join

class Scan():#helping class for easyer use of the scan funktionality of mcstas, needs start and stop value and the unit of the values as well the numbers of steps
    def __init__(self, start, stop, unit, N):
        self.start = start
        self.stop = stop
        self.range = stop-start
        self.unit = unit
        self.N = N
        self.mc = '{},{}'.format(start, stop)
        self.step = (stop-start) / (N-1)
    def absolute_value(self, n):
        return self.step * n + self.start

def which(program):
    if sp.run(["which", program], stdout=sp.DEVNULL, stderr=sp.DEVNULL).returncode == 1:
        sys.exit(f" '{program}' not found or is not an executable")

def execute(command, errormsg, successmsg, print_command=True):
    if print_command:
        print(f"runing: {command}")
    run_return = sp.run(command, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # check if the process was successfully
    if run_return.returncode != 0:
        print(run_return.stdout)
        print(run_return.stderr)
        sys.exit(errormsg)
    else:
        print(f"{successmsg}\n")

def valid_config(var):
    #check dirs
    if not isdir(var.p_local):
        sys.exit(f"the given local working directory '{var.p_local}' dose not exist")
    if not isdir(var.p_server):
        sys.exit(f"the given server working directory '{var.p_server}' dose not exist\n\
                 if you dont intend to use the ssh feature, just set it so valid path")
    if isabs(var.sim_res):
        if not isdir(var.sim_res):
            sys.exit(f"the given simulation result directory '{var.sim_res}' dose not exist")
    else:
        if not isdir(var.p_local/var.sim_res):
            os.mkdir(var.p_local/var.sim_res)
            print(f"created simulation result directory '{var.p_local}' in the local working directory")

def valid_mcconfig(var,mcvar):
    if not mcvar.instr_file.split('.')[1] == "instr":
        sys.exit(f"the given instrument file has not the correct ending:\
                 \nexpected: {mcvar.instr_file.split('.')[0]}.instr\
                 \ngot: {mcvar.instr_file}\
                 \nplease make shure to give a valid instrument file")

    if not isfile(var.p_local/mcvar.instr_file):
        sys.exit(f" the instrument file '{mcvar.instr_file}' dose not exist")

    which(var.mcstas)
    if var.mpi == 0:
        # test if gcc exists
        which("gcc")
    else:
        # test if mpicc exists
        which("mpicc")


# mcstas -t --verbose -o outputfile instrfile (-I componentdir)
def run_mcstas(var, mcvar):
    # create output name
    instr_c_file = mcvar.instr_file.split('.')[0] + ".c"
    # create run_string
    run_string = f"nice {var.mcstas} -t --verbose -o {var.p_local/instr_c_file} {var.p_local/mcvar.instr_file} -I {var.p_local} "
    #if a extra Component Dir is given add the option to the compile command
    if var.componentdir != "":
        run_string = run_string + f"-I {var.componentdir} "
    # exectue the run_string and capture the output
    execute(run_string, "An error occurred while running McStas Compiler", "McStas compiler done")

# gcc (mpicc) -o p_local/reseda.out p_local/reseda.c -lm (-DUSE_MPI) -g -O2 -lm -std=c99
def run_compiler(var,mcvar, cflags=""):
    instr_c_file = mcvar.instr_file.split('.')[0] + ".c"
    instr_out_file = mcvar.instr_file.split('.')[0] + ".out"
    #check if mpi is enabled
    if var.mpi == 0:
        run_string = f"nice gcc "
    else:
        run_string = f"nice mpicc -DUSE_MPI "
    run_string = run_string + f"-o {var.p_local/instr_out_file} {var.p_local/instr_c_file} -lm -g -O2 -std=c99 {cflags}"
    # exectue the run_string and capture the output
    execute(run_string, "An error occurred while running the C Compiler", "C compiler done")

# (mpirun -np 2) instr.out -n -d var=value
def run_instrument(var,mcvar):
    errormsg = "The Simmulation Failed"
    successmsg = "The simmulation compleated successfully"
    instr_out_file = mcvar.instr_file.split('.')[0] + ".out"
    #check if mpi is enabled
    if var.mpi == 0:
        run_string = f"nice {var.p_local/instr_out_file} -n {str(mcvar.n)} "
    else:
        run_string = f"nice mpirun -np {var.mpi} {var.p_local/instr_out_file} -n {str(mcvar.n)} "
    # parsing the parameters and checking if a scan is required
    params = ''
    scan_var = []
    for var_name, var_value in mcvar.__dict__.items():
        if not (var_name in ["scan", "n", "dn", "instr_file"]):
            if isinstance(var_value, Scan):
                scan_var = [var_name, var_value]
            else:
                params = params + f"{var_name}={var_value} "
    # scan or no scan
    if scan_var:
        #scan
        #creating main result directory
        os.mkdir(var.p_local/var.sim_res/mcvar.dn)
        #scanning all points
        print(f"running: {run_string} {scan_var[0]}={scan_var[1].mc} ")
        for i in range (scan_var[1].N):
            print(f"step: {scan_var[0]}={scan_var[1].absolute_value(i)}")
            i_params = params + f"{scan_var[0]}={scan_var[1].absolute_value(i)} "
            final_run_string = run_string + f"-d {str(var.p_local/var.sim_res/mcvar.dn/str(i))} {i_params} "

            execute(final_run_string, errormsg, successmsg, print_command=False)
    else:
        final_run_string = run_string + f"-d {str(var.p_local/var.sim_res/mcvar.dn)} {params} "
        execute(final_run_string, errormsg, successmsg)


def psave(obj, file_path):#saves the given object as a pickle dump in the given file (file gets created)
    f = open(file_path,'xb')
    pickle.dump(obj, f)
    f.close

def pload(file_path):#funktion can read file writen by the psave function and returns its content
    f = open(file_path,'rb')
    obj = pickle.load(f)
    f.close
    return obj

def check_scan(var, mcvar, msg): #ignore for now, is something i might implement later fully
    dir_num = len(os.listdir(var.p_local/var.sim_res/mcvar.dn))
    if dir_num-4 == mcvar.scan.N:
        return True
    else:
        msg = msg + f"the number of result folders dont correspont to the number of steps (#Dir:{dir_num} vs scan.N:{mcvar.scan.N})\n" 
        return False

def is_scan(mcvar):
    for var_name, var_value in mcvar.__dict__.items():
        if not var_name == "scan" and isinstance(var_value,Scan):
            return True
    return False

def check_for_detector_output(var, mcvar):
    if is_scan(mcvar):
        for i in range(mcvar.scan.N):
            if not os.path.isdir(var.p_local/var.sim_res/mcvar.dn/str(i)):
                print(f"the mcstas output dir {mcvar.dn}/{i} dose not exist.\nexiting")
                exit()
    else:
        if not os.path.isdir(var.p_local/var.sim_res/mcvar.dn):
            print(f"the mcstas output dir {mcvar.dn} dose not exist.\n exiting")
            exit()
        else:
            #print("all fine")
            return

def get_result_path_from_input(var, mcvar, msg, args):# logic for retreiveng the correct name for the result foulder
    if args.func == 'analyse':
        if args.result_dir:
            return args.result_dir, msg
        else:
            d = var.p_local/var.sim_res
            return sorted(d.iterdir(), key=os.path.getmtime, reverse=True)[0].name, msg
    if not args.result_dir:
        name = mcvar.dn
    else:
        name = args.result_dir
    if os.path.isdir(var.p_local/var.sim_res/name):
            counter = 0
            new_name = name + "_" + str(counter)
            while os.path.isdir(var.p_local/var.sim_res/new_name):
                counter = counter + 1
                new_name = name + "_" + str(counter)
            msg = f'####################\n new result directory is {new_name}\n####################\n'
            return new_name, msg
    return name, msg
