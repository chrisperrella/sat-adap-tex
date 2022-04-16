import glob, getpass, ctypes
from pathlib import Path
from cv2 import DescriptorMatcher
from grandalf.layouts import SugiyamaLayout
from grandalf.graphs import Vertex, Edge, Graph
from numpy import source

from satadap import bake_cmds

from pysbs import sbsarchive, sbsgenerator
from pysbs.api_exceptions import SBSImpossibleActionError


class NodeHierarchy(object):
	def __init__(self, graph):
		super(NodeHierarchy, self).__init__()
		self.nodes = []
		self.nodes = graph.getNodeList()
	
	def get_edges(self):
		edges = []
		for x, node in enumerate(self.nodes):
			for connected_node in node.getConnectedNodesUID():
				for y, other_node in enumerate(self.nodes):
					if other_node.mUID == connected_node:
						edges.append((x, y))
		return edges


class NodeGraph(Graph):
	def __init_(self):
		super(NodeGraph, self).__init__()
	
	def get_graph_center(self, sub_graph_index):
		pos = [v.view.xy for v in self.C[sub_graph_index].sV]
		center = (sum(x[0] for x in pos) / len(pos), sum(x[1] for x in pos) / len(pos))
		return center


class VertPosition(object):
	def __init__(self, node):
		self.node = node
		self.w, self.h = 144, 144
		pos = self.node.getPosition()
		self.xy = float2(pos[1], -pos[0])


class float2(ctypes.Structure):
	_fields_ = [('x', ctypes.c_float), ('y', ctypes.c_float)]

	def __str__(self):
		return 'x: %f, y: %f' % (self.x, self.y)

	def __getitem__(self, index):
		if index == 0:
			return self.x
		elif index == 1:
			return self.y
		else:
			raise IndexError('Index out of range')


def layout_graph( sbs_graph ):
	hierarchy = NodeHierarchy(sbs_graph)	
	vertices = [Vertex(n) for n in range(len(hierarchy.nodes))]
	edges = [Edge(vertices[v], vertices[w]) for (v, w) in hierarchy.get_edges()]
	graph = NodeGraph(vertices, edges)

	for v in vertices:
		v.view = VertPosition(hierarchy.nodes[v.data])
	
	for subgraph in range(len(graph.C)):
		center = graph.get_graph_center(subgraph)
		roots = list([x for x in graph.C[subgraph].sV if len(x.e_in()) == 0])
		
		layout = SugiyamaLayout(graph.C[subgraph])        
		layout.init_all(roots=roots)
		layout.draw()
		new_center = graph.get_graph_center(subgraph)
		
		if len(hierarchy.nodes) == 1:
			pos = hierarchy.nodes[roots[0].data].getPosition()
			offset = float2(pos[1] - roots[0].view.xy[0], -pos[0] - roots[0].view.xy[1])
		else:
			offset = float2(center[0] - new_center[0], center[1] - new_center[1])

		for i, v in enumerate(graph.C[subgraph].sV):
			v.view.node.setPosition([-v.view.xy[1] - offset[1], v.view.xy[0] + offset[0], 0])


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


def node_connect( graph, source_node, source_output, destination_node, destination_input, num_tries = 0 ):
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
		case_insensitive_destination_inputs = [x.lower() for x in destination_inputs]
		
		if source_output.lower() in case_insensitive_destination_inputs and source_output not in source_outputs:
			source_output = source_outputs[case_insensitive_source_outputs.index(source_output.lower())]
			print(f'[SATADAP] Using case-insensitive match for source output {source_output}')
			node_connect( graph, source_node, source_output, destination_node, destination_input, num_tries )

		if destination_input not in destination_inputs:
			print( f'[SATADAP] {destination_node.getDisplayName()} has no input named {destination_input}' )
			print( f'[SATADAP] Available inputs {destination_inputs}' )
			
		if destination_input.lower() in case_insensitive_destination_inputs  and destination_input not in destination_inputs:
			destination_input = destination_inputs[case_insensitive_destination_inputs.index(destination_input.lower())]
			print(f'[SATADAP] Using case-insensitive match for destination input {destination_input}')
			node_connect( graph, source_node, source_output, destination_node, destination_input, num_tries )
		

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
		#node_connect( graph, multi_material_node, output, output_node, 'inputNodeOutput' )
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
	#These properties should be read off the material config, but I'm feeling lazy tonight
	multi_material_node_params = { 'Materials': 1, 'diffuse': 0, 'specular': 0, 'glossiness': 0, 'ambient_occlusion': 1, 'opacity': 1 } 
	multi_material_node = graph.createCompInstanceNodeFromPath( document, multi_material_node_url, aParameters=multi_material_node_params )

	resource_node_dict = dict()
	create_model_graph_bakers( sbs_context, sbsdoc_path, document, graph, category_dir, meshes_alias_dir, mesh_dict, resource_node_dict, bake_model )

	output_node_dict = dict()
	create_model_graph_outputs( graph, multi_material_node, output_node_dict )
	
	# Add the output combiner node
	output_combiner_node_url = 'utilities://utility_output_combiner.sbs'
	output_combiner_node = graph.createCompInstanceNodeFromPath( document, output_combiner_node_url )
	for output in output_node_dict:
		node_connect( graph, output_combiner_node, output.lower(), output_node_dict[output], 'inputNodeOutput')
		node_connect( graph, multi_material_node, output, output_combiner_node, output)	

	# Composite the baked normal map with the composited materials
	normal_combine_node_url = 'sbs://normal_combine.sbs'
	normal_combine_node_params = { 'blend_quality': 2 }
	normal_combine_node = graph.createCompInstanceNodeFromPath( document, normal_combine_node_url, aParameters=normal_combine_node_params )
	node_connect( graph, output_combiner_node, 'normal', normal_combine_node, 'Input' )
	node_connect( graph, resource_node_dict['Normal Map from Mesh'], 'output', normal_combine_node, 'Input_1' )	
	node_connect( graph, normal_combine_node, 'normal', output_node_dict['Normal'], 'inputNodeOutput' )

	layout_graph( graph )
	document.writeDoc( str(sbsdoc_path) )
	bake_cmds.cook_sbsar( sbs_context, sbsdoc_path ) 