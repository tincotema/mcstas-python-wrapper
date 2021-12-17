# McStas Python Wrapper (mcpw)

On Windows: If you are using the conda powershell delivert with the mcstas installation use this command to install:

	pyhton -m pip install mcpw

this will ensure that it will end in the virtual environment ov the conda shell

## Update Notifications

### 0.2.2->0.3.0:
renamed function: post_mcrun_funktions() to post_simulation()
introduced mandatory function pre_simulation()

Added special function custom():

### 0.4.0:
mcplot now fully supports all forms of scans 

### 0.5.0:
mcvariables and variables are no longer classes but dicts.
This was done due to compatibility problems between simmuations done from command line (mcpw_manager)
and jupyter notebook

Also mcvar.dn is now mcvar['sim']
this should clarify the meaning of this variable as it is the name of a simulation run

mcpw.mcstas_wrapper.is_scan renamed to mcpw.mcstas_wrapper.scan_name

## Requirements

A mcstas instrument with all components

The Define Section of your instrument must have following Format:
	
	DEFINE INSTRUMENT 'instrument'
	(
	    double x = 1.0,     //comment
	
		//comment
	    int i = 1,          //comment
	    float f = 1.0,      //comment
	)

Empty lines will be ignored.

In order to have proper MPI support this script depends on the Open MPI implemenation when using unix based systems.
MPIexec will not work and leads to an error.

## Short Overview

This Package offers several functions to improve your workflow with Mcstas Simuations and
Processing the simmulation results.

The Functionality is build around the two Classes variables and mcvariables.

### Dict variables
Parameters of the dict variables are global variables that apply to any simulation and contains the location of the main working directory.
It is automatically generated with the 'mcpw_setup' command and is saved in local_var.py
It belongs to a single host

The typical name vor this dict is 'var'.

The dict entrys you will find the most usefull will be:

-var['p_local'] The Local Working directory (Absolute Path; a Path object)
-var['sim_res'] The simulation result folder in your p_local dir.

All other variables should not be necessary to use in your code.


### Dict mcvariables
Parameters of the dict mcvariables contain all important values to run a simulation.
The mcpw_setup command will create it from the given instrument file and put it into instrument_name.py file.

The typical name vor the dict is 'mcvar'.

The dict entrys you will find the most usefull will be:

-mcvar['sim'] The directory(name) of a particular simulation

All other entrys should be self explanatory

If one of the variables is an object of the Scan class, the program will run as many simulation steps as defined in the scan variable (see Scan Class below).
You can only scan one variable at a time with this method. To scan multiple variables at once see 'Scaning with csv file'.


### The instrument.py file
The instrument.py file will be the main file you will work in.
Appart from the mcvariables class it will contain all your custom functions
for analysing and datatreatment.
Here you import all necessary packages and all your functions you want to get executed and call them in
the analyse(), pre_simulation() or post_simulation() function.
These three functions will be called by mcpw_manager and executed at the correct time

#### pre_simulation(var,mcvar,var_list)
This function can change var, mcvar, and var_list at runtime before the simulation is called.
You can use it to reformat your var_list, create a new one or have fancy interconecting of your mcstas variables.
The changed variables will later be saved together with the simulation results.
This function is not called if you only analyse a old results.

#### post_simulation(var,mcvar, var_list)
This function is called directly after the simulation and is ment to be a part of postprocessing that permanently change the data from the simulation.
You can for example compress the detector output of several detector to single file to save disk space.

#### analyse(var,mcvar,var_list)
This function should contains everyting to analyse and visualize the results in a non destructive way.
If you use the "full" mode of mcpw_manager it is called at the very end of the simulation also after post_simulation.

You can call it also seperatly for an older simulation you did with the "analyse" mode. 
Here the -d option of mcpw_manager indicates witch old simulation you want to analyse.
The corresponding mcvariables potentially used var_list is automatically loaded. If no -d option is specified the latest available simulation is analysed.

## First Setup

Requirements:

The mcpw_setup command creates all necessary files in order to use the mcpw_manager command.

Go to the directory where your mcstas instrument lies,

Then execute mcpw_setup:

	mcpw_setup -I instrument.instr -d working_directory -m path_to_mcstas_executable -o output_directory -c component_directory

Necessary is only the -I instrument.intr argument.

With the -d working_directory argument you can set a different directory than your current one as the main working directory.

With the -m argument you can give the location of your mcstas installation. only needed if you did not install mcstas with a packages manager.

With the -o argument you can specify the location of the output directory where the simulation results are put in. the default is 'simulation_results' in the main working directory.

With the -c argument you can specify extra locations for mcstas components.

An allrady existing local_var.py or instrument.py file will not be updated or replaced.

If you have no errors and have two files: local_var.py and instrument.py in your working directory the setup step is compleated.

## First Use

With mcpw_manager you can execute your simulation and all relevant functions you added to the analyse and post_mcrun_funktions functions.

The minimal command to run a simmulation is:
	
	mcpw_manager -p instrument.py full

For more advanced usecases have a look at mcpw_manager --help .

## Use of Scan class and var_lists

### Scan Class

The Scan class is used to simplify the process of runing a number of simulations over a range of one variable.
If you want to change more than one variable per step, use the csv file function. 

The first two arguments are the start and stop range for the Scan, the 3th value is a string which represents the unit of the scan variable. the 4th value is the number of steps.
The scan points are evenly distributed between the start and stop points, which are included.

Propertys of the Scan class are:

-scan.start             start value
-scan.stop              stop value
-scan.range             stop - start
-scan.unit              normaly a string that can be used in the automatic labeling of graphs
-scan.N                 number of steps to scan the range with
-scan.step              size of one step
-scan.absolute_value(n) absolute value of the n-th step


### Scaning with csv file

Witch the -l, --list argument you can provide a csv file with datapoints.
The first row has to be a header row containing the names of the variables below them. The names have to match with the once in you instrument.
Each row represents one simulation and has to be fully filled with values that can be cast to a python float.
Variable that dont change at all dont need to be part of the list and will be taken from the mcvariable class.

Mini example csv:

	  x,    y,   z
	  1,    4,   7
	1.4,    6,   9
	  2, 4e-4, 9e5

The content of the csv is loaded into the variable var_list.

If you want to load a csv with a different format than described above, you have to reformat it accordingly inside the scope of the pre_simulation function.

## Jupyter Notebook Usage

This Package can be used also in jupyter notebook.

First you have to import the basic functions initialize, simulate, load_mcvariables:

	from mcpw.jupyter_functions import initialize, simulate, load_mcvariables

Next you have to initialize the local variables:

	var = initialize(instrument='instrument.instr'[, working_dir='relative_or_absolute_path', mcstas='mcstas_path_or_link', output_dir='simulation_results', component_dir='relative_or_absolute_path', mpi=#cores])

The default for mcstas is 'mcstas'
You will get a printout for your mcvariable class. copy the section into the next cell and execute it.

Now var and mcvar should be initialized and you can run a simmulation with:

	mcvar, res = simulate(var, mcvar, sim='bla'[,var_list=[], var_list_csv=PATH])

This function returns the used mcvariables and a list of result directorys where the simulation results are saved.
If the command is called a second time with the same value for dn, the mcvariables and result directorys for this dn will be loaded end returned.
The var_list parameter expects an array in the form discribed above.

If you want to use the default mcstas plotter, you can import it:
	
	from mcpw.mcstas_wrapper import mcplot
	mcplot(var,mcvar)


## Special function custom():
If this function exists in the python file and the mode is set to custom, the compile steps are executed and then the custom function is executed, followed by the analyse function.
This is highly advanced. You need to make shure that the check_for_detector_output function, psave function, and other critical functions are executed.
This function takes the place of the run_instrument() function as well as all save functions.

## List of usefull functions
### General functions

	mcpw.mcstas_wrapper.psave(obj, file_path)
pickle binary dump

	mcpw.mcstas_wrapper.pload(file_path)
pickle binary load (returns a object)

	mcpw.mcstas_wrapper.scan_name(mcvar)
function to determen if a set of mcvariables triggers a Scan
returns the name of the variable to scan or 'False'

	mcpw.mcstas_wrapper.scan(mcvar)
returns the scan object if one was set in the mcvariable dict otherwise 'None'
	

	mcpw.mcstas_wrapper.mcpot(var,mcvar[, mode='qt'])
the original mcplot function


###Functions explicit for jupyter notebook:
Function returning mcvariables from simmulation:

	load_mcvariables(var, sim='')

## Command Usage

### Usage of mcpw_manager
	
	usage: mcpw_manager [-h] -p PYTHON_FILE [-d RESULT_DIR] mode ...
	
	Control command for automatic mcstas usage for the Reseda Instrument
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -p PYTHON_FILE, --python_file PYTHON_FILE
	                        path (absolute or not) to the python file containing mcvariables and analyse functions
	  -d RESULT_DIR, --result-dir RESULT_DIR
	                        directory name for the simulationresults. If none is given or foulder name exists allrady, a increment Folder Name is generated
      -l LIST, --list LIST  a file containing variables in csv format. first row has to match with variable names occuring in the instrument. variables that are not in here take the value from the py file. each row is a single simmulation.
                            list will be saved together with the result for later use 

	modes:
	  Use 'manager mode --help' to view the help for any command.
	
	  mode
	    server              mcstas will be executed localy and the processed simulation results packed in a tarball
	    remote              mcstas will be executed on a remote machine
	    local               mcstas will be executed on localy
	    full                mcstas will be executed on localy and the analyze function will be called after
	    analyse             analyse function will be called
		custom              runs the mcstas compiler, c compiler and a everyting that is in the function called custom in your python file. analyse function will be called !!!EXTREMLY EXPERIMENTAL!!!

### Usage of mcpw_setup
	
	usage: mcpw_setup [-h] -I INSTRUMENT [-d WORKING_DIR] [-m MCSTAS] [-o OUTPUT_DIR] [-c COMPONENT_DIR] mode ...
	
	Script to create a python file to control a McStas Instrument with MPW
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -I INSTRUMENT, --instrument INSTRUMENT
	                        mcstas instrument you want to control with mpw
	  -d WORKING_DIR, --working_dir WORKING_DIR
	                        path to working directory (optional)
	  -m MCSTAS, --mcstas MCSTAS
	                        path to mcstas executable; default=mcstas
	  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
	                        name in the simulation results directory; default=simulation_results
	  -c COMPONENT_DIR, --component_dir COMPONENT_DIR
	                        additional directory where mcstas will search for components; default=""

