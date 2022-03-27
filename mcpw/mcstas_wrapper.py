import subprocess as sp              #needed to run mcstas
import sys                           #needed to select program mode of this script
import pickle                        #needed to save mcstas variables for later use
import os
from os.path import isfile, isdir, isabs, dirname, basename, splitext, join, islink
import locale
from shutil import copyfile, which
import csv
from datetime import datetime
import re
import numpy as np

class DummyFile(object):
    def write(self, x): pass

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

def scan(mcvar):
    for key,value in mcvar.items():
        if isinstance(value,Scan):
            return value
    print("no object of Class Scan found")
    return None

def execute(command, errormsg, successmsg, print_command=True, verbose=False):
    if print_command:
        print(f"runing: {command}")
    run_return = sp.run(command, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # check if the process was successfully
    if run_return.returncode != 0:
        print(f"\nreturn code:{run_return.returncode}")
        print(f"stdout:\n{run_return.stdout}")
        print(f"stderr:\n{run_return.stderr}\n")
        sys.exit(errormsg)
    else:
        if verbose:
            print(f"\nreturn code:{run_return.returncode}")
            print(f"stdout:\n{run_return.stdout}")
            print(f"stderr:\n{run_return.stderr}\n")
        print(f"{successmsg}\n")
    return run_return

def valid_config(var):
    #check dirs
    if not isdir(var['p_local']):
        sys.exit(f"the given local working directory '{var['p_local']}' dose not exist")
    if not isdir(var['p_server']):
        sys.exit(f"the given server working directory '{var['p_server']}' dose not exist\n\
                 if you dont intend to use the ssh feature, just set it so valid path")
    if isabs(var['sim_res']):
        if not isdir(var['sim_res']):
            sys.exit(f"the given simulation result directory '{var['sim_res']}' dose not exist")
    else:
        if not isdir(var['p_local']/var['sim_res']):
            os.mkdir(var['p_local']/var['sim_res'])
            print(f"created simulation result directory '{var['sim_res']}' in the local working directory")
    if isabs(var['sim_res']): #making shure var['sim_res'] is allways a absolute path
        pass
    else:
        var['sim_res'] = var['p_local']/var['sim_res']

    mcstas = which(var['mcstas'])
    if not mcstas:
        sys.exit(f"\nMcStas is not installed or the Path is inocrrect: {var['mcstas']}")
    if islink(mcstas):
        var['mcstas'] = os.readlink(mcstas)

def valid_mcconfig(var,mcvar):
    if not mcvar['instr_file'].split('.')[1] == "instr":
        sys.exit(f"\nthe given instrument file has not the correct ending:\
                 \nexpected: {mcvar['instr_file'].split('.')[0]}.instr\
                 \ngot: {mcvar['instr_file']}\
                 \nplease make shure to give a valid instrument file")

    if not isfile(var['p_local']/mcvar['instr_file']):
        sys.exit(f"\nthe instrument file '{mcvar['instr_file']}' dose not exist")

    if var['mpi'] == 0:
        # test if gcc exists
        if not which("gcc"):
            sys.exit(f"\ngcc is not installed. please install it")
    else:
        # test if mpicc exists
        if os.name=='nt':
            if not which("mpiexec"):
                sys.exit(f"\nmpiexec is not installed. please install Microsoft MPI form the microsoft website")
        else:
            if not which("mpicc"):
                sys.exit(f"\nmpicc is not installed. please install openmpi")


def max_age_of_file_or_dir_list(file_or_dir_list):
    ages = []
    for entry in file_or_dir_list:
        if entry != '':
            if isdir(entry):
                with os.scandir(entry) as it:
                    for e in it:
                        if e.name.endswith(('.comp','.instr','.h')) and e.is_file():
                            ages.append(os.stat(e).st_mtime)
            else:
                if entry.is_file():
                    ages.append(os.stat(entry).st_mtime)
    return max(ages)

def encode_files_to_local_encoding(file_or_dir_list, output_dir):
    file_list = []
    for entry in file_or_dir_list:
        if entry != '':
            if isdir(entry):
                with os.scandir(entry) as it:
                    for e in it:
                        if e.name.endswith(('.comp','.instr','.h')) and e.is_file():
                            file_list.append(e.path)
            else:
                file_list.append(entry)
    for file in file_list:
        try:
            of = open(file, mode='r', encoding='utf-8')
            content = of.read()
            of.close()
            file_name = basename(file)
            nf = open(f"{output_dir}/{file_name}", mode='w', encoding=locale.getpreferredencoding())
            nf.write(content)
            nf.close()
        except UnicodeDecodeError:
            copyfile(file, output_dir/basename(file))
        except UnicodeEncodeError:
            print(f' sciping {basename(file)}')

# mcstas -t --verbose -o outputfile instrfile (-I componentdir)
def run_mcstas(var, mcvar):
    # create output name
    instr_c_file = mcvar['instr_file'].split('.')[0] + ".c"
    temp_dir = 'temp_encoding'
    #age of current c_file
    if isfile(var['p_local']/instr_c_file):
        c_file_age = os.stat(var['p_local']/instr_c_file).st_mtime
    else:
        c_file_age = -1
    source_age = max_age_of_file_or_dir_list([var['p_local']/mcvar['instr_file'], var['p_local'], var['componentdir'], var['p_local']/'local_var.py'])
    if not (source_age > c_file_age or var['recompile'] or c_file_age < 0) :
        return
    if os.name=='nt':
        os.environ['MCSTAS'] = dirname(var['mcstas'])+'/../lib/'
        if not isdir(var['p_local']/temp_dir):
            os.mkdir(var['p_local']/temp_dir)
        encode_files_to_local_encoding([var['p_local']/mcvar['instr_file'], var['p_local'], var['componentdir']], var['p_local']/temp_dir)
        run_string = f"{var['mcstas']} -t --verbose -o {var['p_local']/instr_c_file} {basename(mcvar['instr_file'])} -I {var['p_local']/temp_dir} "
        # exectue the run_string and capture the output
        print(f"runing: {run_string}")
        run_return = sp.run(run_string, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE, cwd=var['p_local']/temp_dir)
        for file in os.listdir(f"{var['p_local']/temp_dir}"):
            os.remove(f"{var['p_local']/temp_dir/file}")
        os.rmdir(f"{var['p_local']/temp_dir}")
    else:
        # create run_string
        run_string = f"{var['mcstas']} -t --verbose -o {var['p_local']/instr_c_file} {var['p_local']/mcvar['instr_file']} -I {var['p_local']} "
        #if a extra Component Dir is given add the option to the compile command
        if var['componentdir'] != "":
            if isabs(var['componentdir']):
                run_string = run_string + f"-I {var['componentdir']} "
            else:
                run_string = run_string + f"-I {var['p_local']/var['componentdir']} "
        # exectue the run_string and capture the output
        print(f"runing: {run_string}")
        run_return = sp.run(run_string, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # check if the process was successfull
    if run_return.returncode != 0:
        print(f"\nreturn code:{run_return.returncode}\n")
        print(run_return.stdout)
        print(run_return.stderr)
        sys.exit("An error occurred while running McStas Compiler")
    else:
        if var["verbose"]:
            print(f"\nreturn code:{run_return.returncode}\n")
            print(run_return.stdout)
            print(run_return.stderr)
        print(f"McStas compiler done\n")

# gcc (mpicc) -o p_local/reseda.out p_local/reseda.c -lm (-DUSE_MPI) -g -O2 -lm -std=c99
def run_compiler(var,mcvar, cflags=""):
    instr_c_file = mcvar['instr_file'].split('.')[0] + ".c"
    if os.name=='nt':
        instr_out_file = mcvar['instr_file'].split('.')[0] + ".exe"
    else:
        instr_out_file = mcvar['instr_file'].split('.')[0] + ".out"

    #check if compiling is necessary
    c_file_age = os.stat(var['p_local']/instr_c_file).st_mtime
    instr_out_file_age = os.stat(var['p_local']/instr_out_file).st_mtime
    if not c_file_age > instr_out_file_age:
         return
    #check if mpi is enabled
    if var['mpi'] == 0:
        run_string = f"gcc "
    else:
        if os.name=='nt':
            run_string = f"{dirname(var['mcstas'])}/mpicc.bat -DUSE_MPI "
        else:
            run_string = f"mpicc -DUSE_MPI "
    run_string = run_string + f"-o {var['p_local']/instr_out_file} {var['p_local']/instr_c_file} -lm -g -O2 -std=c99 {cflags}"
    # exectue the run_string and capture the output
    execute(run_string, "An error occurred while running the C Compiler", "C compiler done", verbose=var["verbose"])

# (mpirun -np 2) instr.out -n -d var=value
def run_instrument(var,mcvar,var_list):
    if os.name == "nt":
        sys.path.append(f"{os.path.dirname(var['mcstas'])}/../lib/tools/Python/mcrun")
    else:
        sys.path.append(f"{os.path.dirname(var['mcstas'])}/../tools/Python/mcrun")
    from mccode import McStasResult
    errormsg = "The Simmulation Failed"
    successmsg = "The simmulation compleated successfully"
    no_use_vars = ["scan", "n", "sim", "instr_file"]
    if os.name=='nt':
        instr_out_file = mcvar['instr_file'].split('.')[0] + ".exe"
    else:
        instr_out_file = mcvar['instr_file'].split('.')[0] + ".out"
    params = ''
    scan_var = []
    res_list = []
    #check if mpi is enabled
    if var['mpi'] == 0:
        run_string = f"{var['p_local']/instr_out_file} -n {str(mcvar['n'])} "
    else:
        if os.name=='nt':
            run_string = f"mpiexec -np {var['mpi']} {var['p_local']/instr_out_file} -n {str(mcvar['n'])} "
        else:
            run_string = f"mpirun --use-hwthread-cpus -np {var['mpi']} {var['p_local']/instr_out_file} -n {str(mcvar['n'])} "
    # parsing the parameters and checking if a scan is required
    for var_name, var_value in mcvar.items():
    #for var_name, var_value in mcvar.__dict__.items():
        if not (var_name in no_use_vars):
            if isinstance(var_value, Scan):
                scan_var = [var_name, var_value]
            else:
                params = params + f"{var_name}={var_value} "
    # scan or no scan
    if var_list:
        params = ''
        dets_vals = []
        #creating main result directory
        os.mkdir(var['sim_res']/mcvar['sim'])
        for name in var_list[0]:
            no_use_vars.append(name)
        for i in range(len(var_list)-1):
            value_list=[]
            print(f"step:{i+1}/{len(var_list)-1}")
            for j, name in enumerate(var_list[0]):
                params = params + f"{name}={var_list[i+1][j]} "
                value_list.append(str(var_list[i+1][j]))
            for var_name, var_value in mcvar.items():
            #for var_name, var_value in mcvar.__dict__.items():
                if not (var_name in no_use_vars):
                    if isinstance(var_value, Scan):
                        sys.exit("VALUE ERROR: You can not have a Scan and the list opiton at the same time.\n Exiting")
                    else:
                        params = params + f"{var_name}={var_value} "
            final_run_string = run_string + f"-d {str(var['sim_res']/mcvar['sim']/str(i))} {params} "

            out = execute(final_run_string, errormsg, successmsg, print_command=False, verbose=var['verbose'])
            temp = sys.stdout
            sys.stdout = DummyFile()
            dets=McStasResult(out.stdout).get_detectors()
            sys.stdout = temp
            for det in dets:
                #print(f'det.intensity: {det.intensity}, det.error: {det.error}')
                value_list.append(str(det.intensity))
                value_list.append(str(det.error))
            res_list.append(var['sim_res']/mcvar['sim']/str(i))
            dets_vals.append(value_list)
        create_sim_file(dets, var, mcvar, var_list)
        create_dat_file(dets, var, mcvar, var_list, dets_vals)

    elif scan_var:
        #scan
        #creating main result directory
        os.mkdir(var['sim_res']/mcvar['sim'])
        dets_vals = []
        #scanning all points
        print(f"running: {run_string} {scan_var[0]}={scan_var[1].mc}\n")
        for i in range (scan_var[1].N):
            value_list=[str(scan_var[1].absolute_value(i))]
            print(f"step: {scan_var[0]}={scan_var[1].absolute_value(i)}")
            i_params = params + f"{scan_var[0]}={scan_var[1].absolute_value(i)} "
            final_run_string = run_string + f"-d {str(var['sim_res']/mcvar['sim']/str(i))} {i_params} "

            temp = sys.stdout
            sys.stdout = DummyFile()
            out = execute(final_run_string, errormsg, successmsg, print_command=False, verbose=var['verbose'])
            dets=McStasResult(out.stdout).get_detectors()
            sys.stdout = temp
            for det in dets:
                value_list.append(str(det.intensity))
                value_list.append(str(det.error))
            res_list.append(var['sim_res']/mcvar['sim']/str(i))
            dets_vals.append(value_list)
        create_sim_file(dets, var, mcvar, var_list)
        create_dat_file(dets, var, mcvar, var_list, dets_vals)
    else:
        final_run_string = run_string + f"-d {str(var['sim_res']/mcvar['sim'])} {params} "
        execute(final_run_string, errormsg, successmsg, verbose=var['verbose'])
        res_list.append(var['sim_res']/mcvar['sim'])
    return res_list

def psave(obj, file_path):#saves the given object as a pickle dump in the given file (file gets created)
    if obj:
        f = open(file_path, mode='xb')
        pickle.dump(obj, f)
        f.close

def pload(file_path):#funktion can read file writen by the psave function and returns its content
    f = open(file_path, mode='rb')
    obj = pickle.load(f)
    f.close
    return obj

def load_var_list(file_path):
    var_list = []
    with open(file_path, newline='') as csvfile:
        csvdata = csv.reader(csvfile)# delimiter=',', quotechar='|')
        for row in csvdata:
            var_list.append(row)
    for x in range(len(var_list)-1):
        for y in range(len(var_list[0])):
            var_list[x+1][y] = float(var_list[x+1][y])
    return var_list

def save_var_list(var_list, filename):
    with open(filename, mode='w') as csvfile:
        w = csv.writer(csvfile)
        for i in range(len(var_list)):
            w.writerow(var_list[i])

def check_scan(var, mcvar, msg): #ignore for now, is something i might implement later fully
    dir_num = len(os.listdir(var['sim_res']/mcvar['sim']))
    if dir_num-4 == scan(mcvar).N:
        return True
    else:
        msg = msg + f"the number of result folders dont correspont to the number of steps (#Dir:{dir_num} vs scan.N:{scan(mcvar).N})\n"
        return False

def scan_name(mcvar):
    for var_name, var_value in mcvar.items():
    #for var_name, var_value in mcvar.__dict__.items():
        if not var_name == "scan" and isinstance(var_value,Scan):
            return var_name
    return False

def check_for_detector_output(var, mcvar, var_list):
    if var_list:
        for i in range(len(var_list)-1):
            if not os.path.isdir(var['sim_res']/mcvar['sim']/str(i)):
                print(f"the mcstas output dir {mcvar['sim']}/{i} dose not exist.\nexiting")
                exit()
    elif scan_name(mcvar):
        for i in range(scan(mcvar).N):
            if not os.path.isdir(var['sim_res']/mcvar['sim']/str(i)):
                print(f"the mcstas output dir {mcvar['sim']}/{i} dose not exist.\nexiting")
                exit()
    else:
        if not os.path.isdir(var['sim_res']/mcvar['sim']):
            print(f"the mcstas output dir {mcvar['sim']} dose not exist.\n exiting")
            exit()
        else:
            #print("all fine")
            return

def get_result_path_from_input(var, mcvar, msg, args):# logic for retreiveng the correct name for the result foulder
    if args.func == 'analyse':
        if args.result_dir:
            return args.result_dir, msg
        else:
            d = var['sim_res']
            return sorted(d.iterdir(), key=os.path.getmtime, reverse=True)[0].name, msg
    if not args.result_dir:
        name = mcvar['sim']
    else:
        name = args.result_dir
    if os.path.isdir(var['sim_res']/name):
            counter = 0
            new_name = name + "_" + str(counter)
            while os.path.isdir(var['sim_res']/new_name):
                counter = counter + 1
                new_name = name + "_" + str(counter)
            msg = f'####################\n new result directory is {new_name}\n####################\n'
            return new_name, msg
    return name, msg

def mcplot(var,mcvar,msg='', mode='qt'):
    if mode == 'qt':
        run_string= f"{dirname(var['mcstas'])}/mcplot-pyqtgraph "
    else:
        run_string= f"{dirname(var['mcstas'])}/mcplot-matplotlib "
    run_string=run_string+f"{var['sim_res']/mcvar['sim']}"
    sp.run(run_string, shell=True)



def create_sim_file(dets, var, mcvar,var_list):
    if var_list:
        steps = len(var_list)-1
        scan_names = ", ".join(var_list[0])
        params = ""
        for i in range(len(var_list[0])):
            #print(f' {var_list[0][i]} = {var_list[1][i]}, {var_list[0][i]} = {var_list[-1][i]},')
            params+=f' {var_list[0][i]} = {var_list[1][i]}, {var_list[0][i]} = {var_list[-1][i]},'
        params = params[:-1] # removing last comma
        xlimits = f' {var_list[1][0]} {var_list[-1][0]}'
    else:
        steps = scan(mcvar).N
        scan_names = scan_name(mcvar)
        params = f" {scan_names} = {scan(mcvar).start}, {scan_names} = {scan(mcvar).stop}"
        xlimits = f" {scan(mcvar).start} {scan(mcvar).stop}"
    lines = []
    lines.append(f'begin instrument:')
    version = execute(f"{var['mcstas']} -v", "","",print_command=False).stdout.split(" ")[2]
    lines.append(f'  Creator: mcstas {version}')
    lines.append(f"  Source: {mcvar['instr_file']}")
    lines.append(f'  Parameters: {scan_names}')
    lines.append(f'  Trace_enabled: no')
    lines.append(f'  Default_main: yes')
    lines.append(f'  Embedded_runtime: yes')
    lines.append(f'end instrument:')
    lines.append(f'')
    lines.append(f'begin simulation')
    lines.append(f'Date: {datetime.strftime(datetime.now(),"%a %b %d %H %M %Y")}')
    lines.append(f"Ncount: {mcvar['n']}")
    lines.append(f'Numpoints: {steps}')
    lines.append(f'Param:{params}')
    lines.append(f'end simulation')
    lines.append(f'')
    lines.append(f'begin data')
    lines.append(f'type: multiarray_1d({steps})')
    lines.append(f'title: Scan of {scan_names}')
    lines.append(f'xvars: {scan_names}')
    det_string=""
    variables_string=""
    for det in dets:
        det_string+= f' ({det.name}_I,{det.name}_ERR)'
        variables_string+= f' {det.name}_I {det.name}_ERR'
    lines.append(f'yvars:{det_string}')
    lines.append(f"xlabel: '{scan_names}'")
    lines.append(f"ylabel: 'Intensity'")
    lines.append(f'xlimits:{xlimits}')
    lines.append(f'filename: mccode.dat')
    lines.append(f'variables: {scan_names.replace(",","")}{variables_string}')
    lines.append(f'end data')

    with open(var['sim_res']/mcvar['sim']/'mccode.sim', "w") as simfile:
        for line in lines:
            simfile.write("{}\n".format(line))

def create_dat_file(dets, var, mcvar, var_list, dets_vals):
    if var_list:
        steps = len(var_list)-1
        scan_names = ", ".join(var_list[0])
        params = ""
        for i in range(len(var_list[0])):
            params+=f' {var_list[0][i]} = {var_list[1][i]},'
        params = params[:-1] # removing last comma
        xlimits = f' {var_list[1][0]} {var_list[-1][0]}'
    else:
        steps = scan(mcvar).N
        scan_names = scan_name(mcvar)
        params = f" {scan_names} = {scan(mcvar).start}"
        xlimits = f" {scan(mcvar).start} {scan(mcvar).stop}"
    lines = []
    lines.append(f"# Instrument-source: '{mcvar['instr_file']}'")
    lines.append(f'# Date: {datetime.strftime(datetime.now(),"%a %b %d %H %M %Y")}')
    lines.append(f"# Ncount: {mcvar['n']}")
    lines.append(f'# Numpoints: {steps}')
    lines.append(f'# Param:{params}')
    lines.append(f'# type: multiarray_1d({steps})')
    lines.append(f'# title: Scan of {scan_names}')
    lines.append(f"# xlabel: '{scan_names}'")
    lines.append(f"# ylabel: 'Intensity'")
    lines.append(f'# xvars: {scan_names}')
    det_string=""
    variables_string=""
    for det in dets:
        det_string+= f' ({det.name}_I,{det.name}_ERR)'
        variables_string+= f' {det.name}_I {det.name}_ERR'
    lines.append(f'# yvars:{det_string}')
    lines.append(f'# xlimits:{xlimits}')
    lines.append(f'# filename: mccode.dat')
    lines.append(f'# variables: {scan_names.replace(",","")}{variables_string}')
    for row in dets_vals:
        lines.append(f'{" ".join(row)}')

    with open(var['sim_res']/mcvar['sim']/'mccode.dat', "w") as simfile:
        for line in lines:
            simfile.write("{}\n".format(line))

def return_detector(var,mcvar, detector, N=-1, plot=None):
    path = ""
    if N>=0:
        path = var['sim_res']/mcvar['sim']/str(N)/detector
        if not isfile(path):
            sys.exit(f'error: File "{path}" dose not exist or is no file.')
    else:
        path = var['sim_res']/mcvar['sim']/detector
        if not isfile(path):
            sys.exit(f'error: File "{path}" dose not exist or is no file.')
    readout =  np.squeeze(np.loadtxt(path))
    with open(path) as det_file:
        text = det_file.read()
        if "array_2d" in text:
            try:
                freetext_pat = '.+'
                comments = {}

                m = re.search('\# title: (%s)' % freetext_pat, text)
                comments["title"] = m.group(1)

                '''# xlabel: Wavelength [AA]'''
                m = re.search('\# xlabel: (%s)' % freetext_pat, text)
                comments["xlabel"] = m.group(1)
                '''# ylabel: Intensity'''
                m = re.search('\# ylabel: (%s)' % freetext_pat, text)
                comments["ylabel"] = m.group(1)
                m = re.search('\# zlabel: (%s)' % freetext_pat, text)
                comments["zlabel"] = m.group(1)

                '''# xvar: L'''
                m = re.search('\# xvar: (%s)' % freetext_pat, text)
                comments["xvar"] = m.group(1)
                '''# zvar: I '''
                m = re.search('\# zvar: (%s)' % freetext_pat, text)
                comments["zvar"] = m.group(1)
                '''# yvar: (I,I_err)'''
                m = re.search('\# yvar: (%s)' % freetext_pat, text)
                comments["yvar"] = m.group(1)

                '''
                # xylimits: -30 30 -30 30
                # xylimits: 0 5e+06 0.5 100
                '''
                m = re.search('\# xylimits: ([\d\.\-\+e]+) ([\d\.\-\+e]+) ([\d\.\-\+e]+) ([\d\.\-\+e]+)([\ \d\.\-\+e]*)', text)
                comments["xylimits"] = (float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))

                '''# values: 6.72365e-17 4.07766e-18 4750'''
                m = re.search('\# values: ([\d\-\+\.e]+) ([\d\-\+\.e]+) ([\d\-\+\.e]+)', text)
                comments["vaules"] = (float(m.group(1)), float(m.group(2)),float(m.group(3)))
                '''# statistics: X0=5.99569; dX=0.0266368;'''
                m = re.search('\# statistics: X0=([\d\.\+\-e]+); dX=([\d\.\+\-e]+); Y0=([\d\.\+\-e]+); dY=([\d\.\+\-e]+);', text)
                comments["statistics"] = f'X0={m.group(1)}; dX={m.group(2)}; Y0={m.group(3)}; dY={m.group(4)}'
                '''# signal: Min=0; Max=1.20439e-18; Mean=4.10394e-21;'''
                m = re.search('\# signal: Min=([\ \d\.\+\-e]+); Max=([\ \d\.\+\-e]+); Mean=([\ \d\.\+\-e]+);', text)
                comments["signal"] = f'Min={m.group(1)}; Max={m.group(2)}; Mean={m.group(3)}'
            except Exception as e:
                print(e)
                sys.exit(f"error while parsing detector {detctor}. Please ensure the format is correct.")
            intensity = []
            intensity.append(readout[0:int(len(readout)/3)])
            intensity.append(readout[int(len(readout)/3):int(len(readout)*2/3)])
            intensity.append(readout[int(len(readout)*2/3):int(len(readout))])
            if plot:
                plot.imshow(intensity[0], extent=comments["xylimits"])
                plot.set_xlabel(comments["xlabel"])
                plot.set_ylabel(comments["ylabel"])
                plot.set_title(comments["title"])
            return intensity, comments
        if "array_1d" in text:
            try:
                freetext_pat = '.+'
                comments = {}
                m = re.search('\# title: (%s)' % freetext_pat, text)
                comments["title"] = m.group(1)
                '''# xlabel: Wavelength [AA]'''
                m = re.search('\# xlabel: (%s)' % freetext_pat, text)
                comments["xlabel"] = m.group(1)
                '''# ylabel: Intensity'''
                m = re.search('\# ylabel: (%s)' % freetext_pat, text)
                comments["ylabel"] = m.group(1)

                '''# xvar: L'''
                m = re.search('\# xvar: ([\w]+)', text)
                comments["xvar"] = m.group(1)
                '''# xlimits: 5.5 6.5'''
                m = re.search('\# xlimits: ([\d\.\-\+e]+) ([\d\.\-\+e]+)', text)
                comments["xlimits"] = (float(m.group(1)),float(m.group(2)))

                '''# yvar: (I,I_err)'''
                m = re.search('\# yvar: \(([\w]+),([\w]+)\)', text)
                comments["yvar"] = (m.group(1),m.group(2))

                '''# values: 6.72365e-17 4.07766e-18 4750'''
                m = re.search('\# values: ([\d\-\+\.e]+) ([\d\-\+\.e]+) ([\d\-\+\.e]+)', text)
                comments["vaules"] = (float(m.group(1)), float(m.group(2)),float(m.group(3)))
                '''# statistics: X0=5.99569; dX=0.0266368;'''
                m = re.search('\# statistics: X0=([\d\.\-\+e]+); dX=([\d\.\-\+e]+);', text)
                comments["statistics"] = f'X0={m.group(1)}; dX={m.group(2)}'
                '''# signal: Min=0; Max=1.20439e-18; Mean=4.10394e-21;'''
                m = re.search('\# signal: Min=([\ \d\.\+\-e]+); Max=([\ \d\.\+\-e]+); Mean=([\ \d\.\+\-e]+);', text)
                comments["signal"] = f'Min={m.group(1)}; Max={m.group(2)}; Mean={m.group(3)}'
            except Exception as e:
                print(e)
                sys.exit(f"error while parsing detector {detctor}. Please ensure the format is correct.")
            if plot:
                xy=np.swapaxes(readout,0,1)
                plot.errorbar(xy[0],xy[1],yerr=xy[2])
                plot.set_xlabel(comments["xlabel"])
                plot.set_ylabel(comments["ylabel"])
                plot.set_title(comments["title"])
            return np.swapaxes(readout, 0, 1), comments
