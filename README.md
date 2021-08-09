# McStas Python Wrapper (mcpw)

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

empty lines will be ignored


## Short Overview

This Package offers several functions to improve your workflow with Mcstas Simuations and
Processing the simmulation results.

The Functionality is build around the two Classes variables and mcvariables.

### class variables
variables are global variables that apply to any simulation and contains the location of the main working directory.
it is automatically generated with the 'mcpw_setup' command and is saved in local_var.python_requires

### class mcvariables
mcvariables contains all important variables to run a simulation.
the mcpw_setup command will create it from the given instrument file and put it into instrument_name.py file.

### the instrument.py file
the instrument.py file will be the main file you will work in.
appart from the mcvariables class it will contain all your custom functions
for analysing and datatreatment.
here you import all necessary packages and all your functions you want to get executed you add into
the analyse() function or the post_mcrun_funktions() function.
the analyse and post_mcrun_funktions will be called by mcpw_manager and executed


## First Setup

Requirements:

the mcpw_setup command creates all necessary files in order to use the mcpw_manager command.

cd to the directory where your mcstas instrument lies

then execute mcpw_setup:

	mcpw_setup -I instrument.instr -d working_directory -m path_to_mcstas_executable -o output_directory -c component_directory

necessary is only the -I instrument.intr argument.

with the -d working_directory argument you can set a different directory than your current one as the main working directory

with the -m argument you can give the location of your mcstas installation. only needed if you did not install mcstas with a packages manager

with the -o argument you can specify the location of the output directory where the simulation results are put in. the default is 'simulation_results' in the main working directory

with the -c argument you can specify extra locations for mcstas components


if you have no errors and have two files: local_var.py and instrument.py in your working directory the setup stepp is compleated

## First Use

with mcpw_manager you can execute your simulation and all relevant functions you added to the analyse and post_mcrun_funktions functions.

the minimal command to run a simmulation is:
	
	mcpw_manager -p instrument.py local




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
	
	modes:
	  Use 'manager mode --help' to view the help for any command.
	
	  mode
	    server              mcstas will be executed localy and the processed simulation results packed in a tarball
	    remote              mcstas will be executed on a remote machine
	    local               mcstas will be executed on localy
	    full                mcstas will be executed on localy and the analyze function will be called after
	    analyse             analyse function will be called

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

