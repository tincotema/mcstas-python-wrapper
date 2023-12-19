# McStas Python Wrapper (mcpw)

## Content

[Why jet an other python wrapper](https://github.com/tincotema/mcstas-python-wrapper/wiki/Why-jet-an-other-python-wrapper%3F)

[Installation](https://github.com/tincotema/mcstas-python-wrapper/wiki/Installation)

[Key Functionalites](https://github.com/tincotema/mcstas-python-wrapper/wiki/Overview-of-Functionality)

[Jupyter Notebook](https://github.com/tincotema/mcstas-python-wrapper/wiki/Jupyter-Notebook)

[Command Usage](https://github.com/tincotema/mcstas-python-wrapper/wiki/Command-Usage)

[Function overview](https://github.com/tincotema/mcstas-python-wrapper/wiki/Function-overview)

[Change log](https://github.com/tincotema/mcstas-python-wrapper/wiki/Change-log)

## Quick start
### Requirements
- mcstas
- gcc
- numpy
- matplotlib

### Instalatlion
- Install with `pip install mcpw`

### First setup

- Enter the directory with your mcstas instrument
- run `mcpw_setup -I 'your_instrument.instr' -m 'path_to_mcstas_executable'`

### Final step
- run `mcpw_manager -p 'your_instrument.py' full`

For more detailed instructions see the Install section and the rest of the Wiki at github.
