import os, subprocess
from pathlib import Path

from pysbs import context, substance, sbsenum, batchtools
from pysbs.api_exceptions import SBSIncompatibleVersionError


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
	sbsdoc = substance.SBSDocument( sbs_context, str( sbsdoc_path ) )
	sbsdoc.parseDoc()

	cmdline = [sbs_context.getBatchToolExePath( sbsenum.BatchToolsEnum.COOKER ),
			   '--quiet',
			   '--enable-icons',
			   '--inputs', str( sbsdoc_path ) ]
	
	subprocess.run( cmdline )


def cook_sbsar( sbs_context, sbsdoc_path, output_path = None ):	
	if output_path is None:
		output_path = sbsdoc_path.parent

	sbsdoc = substance.SBSDocument( sbs_context, str( sbsdoc_path ) )
	
	try:
		sbsdoc.parseDoc()
	except SBSIncompatibleVersionError:
		update_sbs( sbsdoc_path )
		sbsdoc.parseDoc()

	batchtools.sbscooker(quiet =True,
                         inputs = str( sbsdoc_path ),
                         includes = sbs_context.getDefaultPackagePath(),
                         alias = sbs_context.getUrlAliasMgr().getAllAliases(),
                         output_path = str( output_path )).wait()	


def bake_sbsar( sbs_context, sbsdoc_path, identifier, mesh_dict, bake_dict, output_size = 10, bake_arguments = None):
	optional_arguments = ''
	try:
		optional_arguments = bake_dict['BakeArguments']
	except KeyError:
		pass

	cmdline = [sbs_context.getBatchToolExePath( sbsenum.BatchToolsEnum.BAKER ),
	           bake_dict['BakeTool'],
			   '--output-name', f'{bake_dict["Operation"]}',
			   f'{" ".join(optional_arguments)} {" ".join(bake_arguments)}',
			   '--apply-diffusion', 'false',
			   '--antialiasing', '2',
			   '--inputs', str(mesh_dict['LowRes']),
			   '--highdef-mesh', str(mesh_dict['HighRes']),
			   '--output-size', str(output_size),
			   '--dilation-width', '128',
			   '--output-path', str(Path(sbsdoc_path.parent / f'{identifier}.resources'))]
	
	subprocess.run( cmdline )