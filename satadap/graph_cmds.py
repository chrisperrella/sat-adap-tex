from satadap import bake_cmds

from pysbs import sbsarchive
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
