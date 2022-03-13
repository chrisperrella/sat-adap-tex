from satadap import bake_cmds
from pathlib import Path

test_sbs_path = Path(Path(__file__).parent.parent.absolute(), 'library/materials/default/test_001.sbs')
test_mesh_dict = {
    'Low': Path( Path(__file__).parent.parent.absolute(), 'library/meshes/default/bake_widget_lp.fbx' ),
    'High': Path( Path(__file__).parent.parent.absolute(), 'library/meshes/default/bake_widget_hp.fbx' )
}

def test_cook_sbsar(context):
    bake_cmds.cook_sbsar( context, test_sbs_path )


def test_update_sbs(context):
    bake_cmds.update_sbs( context, test_sbs_path )


def test_bake_model(context):
    bakers = ['colorid', 'curvature', 'normal', 'occlusion', 'position', 'wsnormal']
    for baker in bakers:
        output_path = Path(__file__).parent.absolute()
        bake_cmds.bake_model( context, test_mesh_dict['Low'].parent, test_mesh_dict['Low'].stem, baker, test_mesh_dict )


def main():
    context = bake_cmds.spawn_context()
    test_bake_model(context)
    
    
if __name__ == '__main__':
    main()