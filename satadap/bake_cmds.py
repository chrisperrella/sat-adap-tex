import os, subprocess, json
from pathlib import Path

from pysbs import context, substance, sbsenum, batchtools
from pysbs.api_exceptions import SBSIncompatibleVersionError


class BakeModelError(Exception):
	def __init__(self, message='[SATADAP] Baker Config doesnt exist!'):
		super(BakeError, self).__init__(message)


def spawn_context():
	user_sbsprj 	= Path( os.getenv('LOCALAPPDATA'), 'Adobe', 'Adobe Substance 3D Designer', 'user_project.sbsprj' )
	project_manager = context.ProjectMgr(aSbsPrjFilePath=user_sbsprj)
	project_manager.populateUrlAliasesMgr()
	sbs_context = project_manager.getContext()

	#work around for a bug in pysbs on windows
	alias_manager = sbs_context.getUrlAliasMgr()
	for alias in alias_manager.getAllAliases():
		alias_name, alias_path = alias.rsplit(':///')
		alias_manager.setAliasAbsPath(alias_name, alias_path)
	
	return sbs_context


def update_sbs( sbs_context, sbsdoc_path ):	
	batchtools.sbsupdater(quiet =True,
						  inputs = str( sbsdoc_path ),
						  alias = sbs_context.getUrlAliasMgr().getAllAliases()).wait


def cook_sbsar( sbs_context, sbsdoc_path, output_path = None ):	
	if output_path is None:
		output_path = sbsdoc_path.parent

	sbsdoc = substance.SBSDocument( sbs_context, str( sbsdoc_path ) )
	
	try:
		sbsdoc.parseDoc()
	except SBSIncompatibleVersionError:
		update_sbs( sbs_context, sbsdoc_path )
		sbsdoc.parseDoc()

	batchtools.sbscooker(quiet =True,
						 inputs = str( sbsdoc_path ),
						 includes = sbs_context.getDefaultPackagePath(),
						 alias = sbs_context.getUrlAliasMgr().getAllAliases(),
						 output_path = str( output_path )).wait()	


def bake_model( sbs_context, output_path, identifier, operation, mesh_dict, output_size = 10, bake_arguments = ''):
	baker_path = Path( Path(__file__).parent.absolute(), 'bakers', f'{operation}.json')
	if baker_path.is_file:		
		with open(baker_path) as json_file:    
			baker_config = json.load(json_file)

		try:
			optional_arguments = baker_config['Arguments']	
		except KeyError:
			optional_arguments = ''

		output_path = Path(output_path / f'{identifier}.resources')
		output_path.mkdir(parents=True, exist_ok=True)

		cmdline = [sbs_context.getBatchToolExePath( sbsenum.BatchToolsEnum.BAKER ),
					baker_config['Command'],
					'--output-name', f'"{baker_config["Operation"]}"',
					f'{" ".join(optional_arguments)} {" ".join(bake_arguments)}',
					'--apply-diffusion', 'false',
					'--antialiasing', '2',
					'--inputs', str(mesh_dict['Low']),
					'--highdef-mesh', str(mesh_dict['High']),
					'--output-size', f"{output_size},{output_size}",
					'--dilation-width', '128',
					'--output-path', str(output_path)]

		subprocess.run(' '.join(cmdline))

	else:
		raise BakeModelError