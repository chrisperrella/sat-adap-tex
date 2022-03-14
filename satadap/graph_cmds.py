import glob
from pathlib import Path
from os.path import relpath

from satadap import bake_cmds

from pysbs import sbsarchive, sbsgenerator
from pysbs.api_exceptions import SBSImpossibleActionError


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
		graph.connectNodes( source_node, source_output, destination_node, destination_input )
	
	except SBSImpossibleActionError:
		print( f'[SATADAP] Failed to connect {source_node.mUID}.{source_output} -> {destination_node}.{destination_input}' )
		print( f'[SATADAP] Failed to connect {source_node.getDisplayName()} -> {destination_node.getDisplayName()}' )

		source_outputs = list()
		for plug in source_node.getDefinition().mOutputs:
			source_outputs.append( plug.getIdentifierStr() )
		
		destination_inputs = list()
		for plug in destination_node.getDefinition().mInputs:
			destination_inputs.append( plug.getIdentifierStr() )

		if source_output not in source_outputs:		
			print( f'[SATADAP] {source_node.getDisplayName()} has no output named {source_output}' )
			print( f'[SATADAP] Available outputs {source_outputs}' )

		if destination_input not in destination_inputs:
			print( f'[SATADAP] {destination_node.getDisplayName()} has no input named {destination_input}' )
			print( f'[SATADAP] Available inputs {destination_inputs}' )	
		pass


def create_model_graph( sbs_context, sbsdoc_path, mesh_dict, bake_model=True ):
	document = sbsgenerator.createSBSDocument( sbs_context, str(sbsdoc_path.parent), str(sbsdoc_path.stem) )
	graph = document.getSBSGraph( str(sbsdoc_path.stem) )

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
		meshes_alias_path = Path(sbs_context.getUrlAliasMgr().getAliasAbsPath( 'meshes' ))
		resource_path = Path(f'{meshes_alias_path}/{sbsdoc_path.relative_to(meshes_alias_path).parent}/{sbsdoc_path.stem}.resources/{baker_config["Operation"]}.png')
		document.createLinkedResource( str(resource_path),
									   aResourceTypeEnum=3, 
									   aIdentifier=resource_path.stem.replace(' ', '_').lower() )

	document.writeDoc( str(sbsdoc_path) )	