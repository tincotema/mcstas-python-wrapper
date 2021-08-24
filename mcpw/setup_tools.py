'''
class variables():
    def __init__(self):
        #directorys
        self.p_server    = Path("/path/to/working/dir")
        self.p_local     = Path("/path/to/working/dir")
        self.sim_res     = "simulation_results/"
        #ssh related variables
        self.rate        = 32000 #scp transfairrate in bits/s
        self.port        = 22
        self.server      = ""
        #mcstas location
        self.mcstas  = "mcstas"
        #mcstas variables
        self.mpi         = 2
        #additional c compiler flags
        self.cflags      = ""
'''
def create_local_var_lines(args):
    print("generating class variables")
    class_variables_lines = []
    class_variables_lines.append("from pathlib import Path             #needed for the path logic")
    class_variables_lines.append("class variables():")
    class_variables_lines.append("    def __init__(self):")
    class_variables_lines.append("        #directorys")
    class_variables_lines.append(f'        self.p_server     = Path("/")')
    class_variables_lines.append(f'        self.p_local      = Path("{args.working_dir}")')
    class_variables_lines.append(f'        self.sim_res      = "{args.output_dir}"')
    class_variables_lines.append(f"        #ssh related variables")
    class_variables_lines.append(f'        self.rate         = 32000 #scp transfairrate in bits/s')
    class_variables_lines.append(f'        self.port         = 22')
    class_variables_lines.append(f'        self.server       = ""')
    class_variables_lines.append(f"        #mcstas location")
    class_variables_lines.append(f'        self.mcstas       = "{args.mcstas}"')
    class_variables_lines.append(f'        self.componentdir = "{args.component_dir}"')
    class_variables_lines.append(f"        #mcstas variables")
    class_variables_lines.append(f'        self.mpi          = {args.mpi}')
    class_variables_lines.append(f"        #additional c compiler flags")
    class_variables_lines.append(f'        self.cflags       = ""')

    return class_variables_lines

def create_local_var(args):
    class_variables_lines = create_local_var_lines(args)
    with open(f"{args.working_dir}/local_var.py", "w") as pyfile:
        for line in class_variables_lines:
            print(line)
            pyfile.write("{}\n".format(line))

"""
This Script creats a python class contianing all variables,
defined in the DEFINE INSTRUMENT Section of an McStas Instrument File.
The Define Section must have following Format:
---------------------------------------------
DEFINE INSTRUMENT 'instrument'
(
    double x = 1.0,     //comment

    int i = 1,          //comment
    float f = 1.0,      //comment
)
---------------------------------------------
empty lines will be ignored

The Outputformat will be:
---------------------------------------------
class mcvariables():#class to hold the variables needed to run the mcstas simulation
    def __init__(self):
        # allways needed
        self.dn             = 'run1' #name of the result diretory for the run
        self.n              = 1000000 #numbers of neutrons for simulation
        self.N              = 1       #steps (see sweep)
        self.instr_file     = "test.instr" #the name of the instrument file, must be located in p_server/p_local, all custom components used by the instrument must be located in the same diretory
        #
        #self.sweep          = Sweep(-0.1,0.1,'A')
        # variables defined in the DEFINE INSTRUMENT section of the mcstas instrument
        x = 1.0,        //comment
        i = 1,          //comment
        f = 1.0,        //comment

post_mcrun_funktions(var, mcvar):
    func1(var, mcvar)
    func2(var, mcvar)

analyse(var,mcvar):
    func1(var, mcvar)
    ...
    funcX(var,mcvar)

---------------------------------------------
"""
import sys
from os.path import isfile, basename
def check_args(args):
    if not args.instrument.endswith(".instr"):
        sys.exit(f"{args.instrument} dose not end on .instr")
    if not isfile(args.working_dir +'/'+ args.instrument):
        sys.exit(f" the instrument file '{args.instrument}' is not located in the working directory '{args.working_dir}'")



def create_class_mcvariables_lines(instrument):
    var_lines = []
    with open(instrument) as mcfile:
        befor_define_section = True
        in_define_section = False
        for line in mcfile:
            if befor_define_section:
                if line.startswith("DEFINE INSTRUMENT"):
                    befor_define_section = False
                    in_define_section = True
            if in_define_section:
                if line == ")\n":
                    in_define_section = False
                if (line != "(\n") and not line.startswith("DEFINE INSTRUMENT") and line !="\n" and line !=")\n":
                    var_lines.append(line.replace("\t","    ").replace("\n","").replace(","," ").replace("//","#").lstrip().split(' ',1)[1])

    class_mcvariables_lines = []
    class_mcvariables_lines.append("class mcvariables():#class to hold the variables needed to run the mcstas simulation")
    class_mcvariables_lines.append("    def __init__(self):")
    class_mcvariables_lines.append("        # allways needed")
    class_mcvariables_lines.append('        self.dn             = "default"')
    class_mcvariables_lines.append("        self.n              = 1000000")
    class_mcvariables_lines.append(f'        self.instr_file     = "{basename(instrument)}"  #the name of the instrument file, must be located in p_server/p_local')
    class_mcvariables_lines.append("        self.scan           = Scan(-0.1,0.1,'A', 3) # (begining, ending, Unit, number of steps)")
    class_mcvariables_lines.append("        #variables defined in the DEFINE INSTRUMENT section of the mcstas instrument")
    for line in var_lines:
        if line.__contains__("="):
            class_mcvariables_lines.append(f"        self.{line}")
        else:
            class_mcvariables_lines.append(f"        # {line}")

    return class_mcvariables_lines

def create_header_lines():
    header_lines = []
    header_lines.append(f'# import section')
    header_lines.append(f'from mcpw.mcstas_wrapper import Scan')
    header_lines.append(f'')
    header_lines.append(f'#this file must allways contain:')
    header_lines.append(f'#class mcvariables() a class containing all parameters for the mcstas instrument file')
    header_lines.append(f'#def post_mcrun_funktions(var,mcvar) a funcition containing all functions that should be exectuded directly after mcstas has been executed')
    header_lines.append(f'#def analyse(var,mcvar) a funcition containing all functions that should be exectuded to analyse a finished mcstas simulation')
    return header_lines

def create_main_lines():
    main_lines = []
    main_lines.append(f'###########################')
    main_lines.append(f'#   your custom function  #')
    main_lines.append(f'###########################')
    main_lines.append(f'')
    main_lines.append(f'def custom_function1(var,mcvar,msg):')
    main_lines.append(f'    print("hallo world 1")')
    main_lines.append(f'')
    main_lines.append(f'def custom_function2(var,mcvar,msg):')
    main_lines.append(f'    print("hallo world 2")')
    main_lines.append(f'')
    main_lines.append(f'')
    main_lines.append(f'##########################################################')
    main_lines.append(f'# adding custom function to corresponding function group #')
    main_lines.append(f'##########################################################')
    main_lines.append(f'')
    main_lines.append(f'# adding functions to post mcstas function group')
    main_lines.append(f'def post_mcrun_funktions(var,mcvar,msg):')
    main_lines.append(f'    custom_function1(var,mcvar,msg)')
    main_lines.append(f'')
    main_lines.append(f'# adding functions to analyse function group')
    main_lines.append(f'def analyse(var,mcvar,msg):')
    main_lines.append(f'    custom_function2(var,mcvar,msg)')
    main_lines.append(f'')
    main_lines.append(f'# end of documentation')

    return main_lines


def create_python_file(args):
    check_args(args)
    header_lines = create_header_lines()
    main_lines = create_main_lines()
    print(f"reading {args.instrument}")
    class_mcvariables_lines = create_class_mcvariables_lines(f"{args.working_dir}/{args.instrument}")

    with open(f"{args.working_dir}/{args.instrument.split('.')[0]}.py", "w") as pyfile:
        for line in header_lines:
            print(line)
            pyfile.write("{}\n".format(line))
        pyfile.write("\n")
        pyfile.write("\n")
        for line in class_mcvariables_lines:
            print(line)
            pyfile.write("{}\n".format(line))
        pyfile.write("\n")
        pyfile.write("\n")
        for line in main_lines:
            print(line)
            pyfile.write("{}\n".format(line))













