from satadap import bake_cmds
from pathlib import Path

def main():
    context = bake_cmds.spawn_context()
    bake_cmds.cook_sbsar( context, Path('C:/sat-adap-tex/library/materials/default/test_001.sbs') )
    
if __name__ == '__main__':
    main()