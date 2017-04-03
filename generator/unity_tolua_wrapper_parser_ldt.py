import re
import os

builtin_types_map = {
	"int": "#number",
	"number": "#number",
	"string": "#string",
	"bool": "#boolean",
	"boolean": "#boolean",
	"float": "#number"
}

def parse(ifile,odir):
	parsing_class = None
	function_defs = {}
	filed_defs = {}

	def cstype_map_to_ldttype(cs_type):
		ldt_type = None
		if cs_type is not None:
			if cs_type in builtin_types_map:
				ldt_type = builtin_types_map[cs_type]
			elif cs_type.endswith("[]"):
				cs_type = cs_type[:-2]
				module = cs_type.replace(".","_")
				_type = cs_type.split(".")[-1]
				ldt_type = "#list<%s>" % (module + "#" + _type)
			else:
				module = cs_type.replace(".","_")
				_type = cs_type.split(".")[-1]
				ldt_type = module + "#" + _type
		return ldt_type

	with open(ifile,"r") as f:
		brace_level = 0
		cs_function_def_parsing_func_name = None
		cs_function_def_breace_level = -1
		cs_function_def_max_args = 0
		cs_function_def_is_static = True
		cs_function_def_return_type = None
		for line in f:
			if line.find("{") > 0: brace_level = brace_level + 1
			if line.find("}") > 0: 
				brace_level = brace_level - 1
				if brace_level == cs_function_def_breace_level and cs_function_def_parsing_func_name is not None:
					# will out c# function
					if cs_function_def_parsing_func_name in function_defs:
						function_def = function_defs[cs_function_def_parsing_func_name]
						function_def["param_count"] = cs_function_def_max_args
						function_def["return_type"] = cstype_map_to_ldttype(cs_function_def_return_type)
						function_def["is_static"] = cs_function_def_is_static
						function_def["valid"] = True
					if cs_function_def_parsing_func_name.startswith("get_"):
						getter_for_func_name = cs_function_def_parsing_func_name[4:]
						if getter_for_func_name in filed_defs:
							filed_def = filed_defs[getter_for_func_name]
							filed_def["type"] = cstype_map_to_ldttype(cs_function_def_return_type)
							filed_def["valid"] = True
					cs_function_def_breace_level = -1

			if cs_function_def_breace_level >= 0:
				# in c# function
				cs_function_def_arg_match = re.search(r'count == (\d+)', line)
				if cs_function_def_arg_match: 
					argc = int(cs_function_def_arg_match.group(1))
					if cs_function_def_max_args < argc:
						cs_function_def_max_args = argc
				cs_function_def_arg_match = re.search(r'CheckArgsCount\(L, (\d+)\)', line)
				if cs_function_def_arg_match: 
					argc = int(cs_function_def_arg_match.group(1))
					if cs_function_def_max_args < argc:
						cs_function_def_max_args = argc
				cs_function_def_instance_method_match = re.search(r' obj = ', line)
				if cs_function_def_instance_method_match:
					cs_function_def_is_static = False
					if cs_function_def_max_args == 0:
						cs_function_def_max_args = 1
				cs_function_def_return_match = re.match(r'^\s*(.*?) o = .*;$', line)
				if cs_function_def_return_match is None:
					cs_function_def_return_match = re.match(r'^\s*(.*?) ret = .*;$', line)
				if cs_function_def_return_match is None:
					cs_function_def_return_match = re.match(r'^\s*LuaDLL\.lua_push(.*?)\(', line)
				if cs_function_def_return_match:
					cs_function_def_return_type = cs_function_def_return_match.group(1)
				continue

			def get_class_name_from_file_name():
				file_name = os.path.basename(ifile)
				if file_name.endswith("Wrap.cs"):
					name = file_name[:-7].replace("_",".")
				return name
			class_def_match = re.match(r'^\s*L\.BeginClass\(typeof\((.*?)\), typeof\((.*?)[,\)]', line)
			if class_def_match:
				assert(parsing_class == None)
				parsing_class = {"name": get_class_name_from_file_name(),
								 "parent": class_def_match.group(2)}

			class_def_match = re.match(r'^\s*L\.BeginClass\(typeof\((.*?)\), null[,\)]', line)
			if class_def_match:
				assert(parsing_class == None)
				parsing_class = {"name": get_class_name_from_file_name()}

			class_def_match = re.match(r'^\s*L\.BeginStaticLibs\("(.*?)"\)', line)
			if class_def_match:
				assert(parsing_class == None)
				parsing_class = {"name": get_class_name_from_file_name()}

			class_def_match = re.match(r'^\s*L\.BeginEnum\(typeof\((.*?)\)', line)
			if class_def_match:
				assert(parsing_class == None)
				parsing_class = {"name": class_def_match.group(1)}

			function_def_match = re.match(r'^\s*L\.RegFunction\("(.*?)"', line)
			if function_def_match: 
				function_name = function_def_match.group(1)
				function_defs[function_name] = {"name": function_name}

			field_def_match = re.match(r'^\s*L\.RegVar\("(.*?)"', line)
			if field_def_match:
				field_name = field_def_match.group(1)
				filed_defs[field_name] = {"name":field_name}

			cs_function_def_match = re.match(r'^\s*static int (.*?)\(', line)
			if cs_function_def_match:
				cs_function_def_parsing_func_name = cs_function_def_match.group(1)
				cs_function_def_breace_level = brace_level
				cs_function_def_max_args = 0
				cs_function_def_is_static = True
				cs_function_def_return_type = None

		# output
		ldt_type = cstype_map_to_ldttype(parsing_class["name"])
		parsing_module = ldt_type.split("#")[0]
		parsing_type = ldt_type.split("#")[1]
		with open(os.path.join(odir,parsing_module+".doclua"),"w") as of:
			of.write("---\n")
			of.write("-- @module %s\n\n" % parsing_module)
			of.write("---\n")
			of.write("-- @type %s\n" % parsing_type)
			if "parent" in parsing_class:
				of.write("-- @extends %s\n" % cstype_map_to_ldttype(parsing_class["parent"]))
			of.write("\n")
			for _, func in function_defs.iteritems():
				if not "valid" in func: continue
				of.write("---\n")
				of.write("-- @function [parent=#%s] %s\n" % (parsing_type, func["name"]))
				if not func["is_static"]:
					of.write("-- @param self\n")
				for i in range(func["param_count"] - (0 if func["is_static"] else 1)):
					of.write("-- @param arg%d\n" % i)
				if func["return_type"] is not None:
					of.write("-- @return %s\n" % func["return_type"])
				of.write("\n")
			for _, field in filed_defs.iteritems():
				if not "valid" in field: continue
				of.write("---\n")
				_type = field["type"] + " " or ""
				of.write("-- @field [parent=#%s] %s%s\n\n" % (parsing_type, _type, field["name"]))
			of.write("return nil\n")

if __name__ == "__main__":
	srcdir1 = r"D:\unity_projects\test2\Assets\Source\Generate"
	srcdir2 = r"D:\unity_projects\test2\Assets\3rd\tolua\ToLua\BaseType"
	destdir = r"D:\unity_projects\test2\Assets\Source\generate_doclua"
	ignore_files = [
		"LuaInterface_LuaOutWrap.cs", 
		"System_Collections_Generic_DictionaryWrap.cs", 
		"System_Collections_Generic_Dictionary_KeyCollectionWrap.cs",
		"System_Collections_Generic_Dictionary_ValueCollectionWrap.cs",
		"System_Collections_Generic_KeyValuePairWrap.cs",
		"System_Collections_Generic_ListWrap.cs",
		"System_Collections_ObjectModel_ReadOnlyCollectionWrap.cs"]
	flist1 = [os.path.join(srcdir1,f) for f in os.listdir(srcdir1)]
	flist2 = [os.path.join(srcdir2,f) for f in os.listdir(srcdir2)]
	for fpath in flist1 + flist2:
		if fpath.endswith("Wrap.cs") and os.path.basename(fpath) not in ignore_files:
			parse(fpath, destdir)