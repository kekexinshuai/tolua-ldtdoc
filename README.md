# tolua ldtdoc
An eclipse-ldt doclua generator for [ToLua#](https://github.com/topameng/tolua)  
I like eclipse lua development tools so did this.  
The generator is just a fancy regex matcher. Nothing special.  
Assuming you have an eclipse lua project already. Just place generated_doclua and doclua in build paths as follows:  
![Project Example](./generator/project_example.png)  
Then enjoy:  
![Auto-complete Example](./generator/autocomplete_example.png)  

# why eclipse
### type hinting
![Type-Hinting Example](./generator/type_hinting_example.png)
### custom type autocompletion support
http://wiki.eclipse.org/LDT/User_Area/Documentation_Language

# debugger
### 1. make debugger recognize unity loaded lua files:
change LuaConst.cs, make openZbsDebugger = true, then apply [this patch](https://github.com/ps5mh/tolua/commit/5ed16e1975c157d3b6d8a843db5a7b528a5ab2fc)
### 2. use the "Lua Attach to Application" configuration.
export a dbgp debugger client from eclipse. And require it in your code when you start the debug session.
```lua
require("ldt_debugger")()
```
### 3. fix for debugger.lua(line number may wrong)
```lua
-- comment out this line if you don't want debugger exits unity when detach
  os.exit(1) -- line 379

-- comment out this line to fix debugger crash when inspect variables
   { tag = "context", attr = { name = "Global",  id = 1 } }, -- line 636
```