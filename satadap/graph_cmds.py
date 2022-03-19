import glob, getpass
from pathlib import Path
from os.path import relpath

from satadap import bake_cmds

from pysbs import sbsarchive, sbsgenerator
from pysbs.api_exceptions import SBSImpossibleActionError


def set_graph_attribute( graph, attribute_dict ):
	for key, value in attribute_dict.items():
		graph.setAttribute( int(key), value )


def get_sbsar_output_nodes( sbs_context, sbsar_path, identifier=None ):
	sbsar_doc = sbsarchive.SBSArchiveDocument( sbs_context, str( sbsar_path ) )
	sbsar_doc.parseDoc()

	graph = sbsar_doc.getFirstSBSGraph()
	if identifier is not None:
		graph = sbsar_doc.getSBSGraph( identifier )

	output_nodes = list()
	for output in graph.getGraphOutputs():
		output_node_name = output.mIdentifier
		output_nodes.append( output_node_name )

	return output_nodes


def node_connect( graph, source_node, source_output, destination_node, destination_input ):
	try:
		graph.connectNodes( source_node, destination_node, source_output, destination_input )
			
	except SBSImpossibleActionError as e:
		print(e)
		print( f'[SATADAP] Failed to connect {source_node.getDisplayName()}.{source_output} -> {destination_node.getDisplayName()}.{destination_input}' )

		source_outputs = list()
		for plug in source_node.getDefinition().mOutputs:
			source_outputs.append( plug.getIdentifierStr() )
		
		destination_inputs = list()
		for plug in destination_node.getDefinition().mInputs:
			destination_inputs.append( plug.getIdentifierStr() )

		if source_output not in source_outputs:		
			print( f'[SATADAP] {source_node.getDisplayName()} has no output named {source_output}' )
			print( f'[SATADAP] Available outputs {source_outputs}' )
			
		case_insensitive_source_outputs = [x.lower() for x in source_outputs]
		if source_output.lower() in case_insensitive_source_outputs:
			source_output = source_outputs[case_insensitive_source_outputs.index(source_output.lower())]
			node_connect( graph, source_node, source_output, destination_node, destination_input )

		if destination_input not in destination_inputs:
			print( f'[SATADAP] {destination_node.getDisplayName()} has no input named {destination_input}' )
			print( f'[SATADAP] Available inputs {destination_inputs}' )	

		case_insensitive_destination_inputs = [x.lower() for x in destination_inputs]
		if source_output.lower() in case_insensitive_destination_inputs:
			destination_input = source_outputs[case_insensitive_destination_inputs.index(destination_inputs.lower())]
			node_connect( graph, source_node, source_output, destination_node, destination_input )


def create_model_graph_bakers( sbs_context, 
								sbsdoc_path, 
								document, 
								graph, 
								category_dir,
								meshes_alias_dir, 
								mesh_dict, 
								resource_node_dict,
								bake_model ):
	baker_config_dir = Path( Path(__file__).parent.absolute(), 'bakers' )
	baker_configs = glob.glob(f"{str(baker_config_dir)}/*.json")
	for baker_config in baker_configs:
		baker_config_path = Path( baker_config )
		operation = baker_config_path.stem		

		if bake_model:
			try:
				baker_config = bake_cmds.bake_model( sbs_context, sbsdoc_path, baker_config_path, mesh_dict )				
			except bake_cmds.BakeModelConfigError:
				print( f'[SATADAP] Failed to bake {baker_config["Operation"]}!' )
				continue

		else:
			import json
			with open(baker_config_path) as json_file:
				baker_config = json.load(json_file)

		print(f'[SATADAP] Linking resources for: {baker_config["Operation"]}')		
		resource_path = Path(meshes_alias_dir, 
							 category_dir, 
							 f'{sbsdoc_path.stem}.resources', 
							 f'{baker_config["Operation"]}.png')
		resource_node = graph.createBitmapNode(document, str(resource_path), aAutodetectImageParameters=True)
		resource_node_dict[baker_config["Operation"]] = resource_node	


def create_model_graph_outputs( graph, multi_material_node, output_node_dict ):
	material_config = bake_cmds.get_material_config()	
	for output in material_config['Outputs'][0]:
		output_node = graph.createOutputNode( output.lower() )
		node_connect( graph, multi_material_node, output, output_node, 'inputNodeOutput' )
		output_node_dict[output] = output_node
	
	return output_node_dict


def create_model_graph( sbs_context, sbsdoc_path, mesh_dict, bake_model=True ):
	meshes_alias_dir = Path( sbs_context.getUrlAliasMgr().getAliasAbsPath( 'meshes' ) )
	category_dir = sbsdoc_path.relative_to( meshes_alias_dir ).parent

	document = sbsgenerator.createSBSDocument( sbs_context, str(sbsdoc_path.parent), str(sbsdoc_path.stem) )
	graph = document.getSBSGraph( str(sbsdoc_path.stem) )

	graph_attribute_dict = { '0' : category_dir.parent, '1' : sbsdoc_path.stem, '2' : getpass.getuser() }
	set_graph_attribute( graph, graph_attribute_dict )

	multi_material_node_url = 'sbs://multi_material_blend.sbs'
	multi_material_node_params = { 'Materials': 1 }
	multi_material_node = graph.createCompInstanceNodeFromPath( document, multi_material_node_url, aParameters=multi_material_node_params )

	resource_node_dict = dict()
	create_model_graph_bakers( sbs_context, sbsdoc_path, document, graph, category_dir, meshes_alias_dir, mesh_dict, resource_node_dict, bake_model )	

	output_node_dict = dict()
	create_model_graph_outputs( graph, multi_material_node, output_node_dict )

	# Composite the baked normal map with the composited materials
	normal_combine_node_url = 'sbs://normal_combine.sbs'
	normal_combine_node = graph.createCompInstanceNodeFromPath( document, normal_combine_node_url, aParameters={ 'blend_quality': 2 } )
	node_connect( graph, multi_material_node, 'Normal', normal_combine_node, 'Input' )
	node_connect( graph, resource_node_dict['Normal Map from Mesh'], 'output', normal_combine_node, 'Input_1' )
	node_connect( graph, normal_combine_node, 'output', output_node_dict['Normal'], 'inputNodeOutput' )

	document.writeDoc( str(sbsdoc_path) )
	bake_cmds.cook_sbsar( sbs_context, sbsdoc_path ) 