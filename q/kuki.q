.kuki.importedModules:("";"");

.kuki.index: .j.k (,/) read0 `:kuki_index.json;

.kuki.appendSlash:{$[not "/"=last x;:x,"/";x]};

.kuki.joinPath:{[path;subPaths]
  $[10h=type subPaths;
    .kuki.appendSlash[path],subPaths;
    (,/)(.kuki.appendSlash each enlist[path],-1_subPaths),-1#subPaths
  ]
 };

.kuki.rootDir: {kukiRoot:getenv`KUKIPATH;$[count kukiRoot;kukiRoot;.kuki.joinPath[getenv`HOME;("kuki")]]}[];


.kuki.getRealPath:{[modulePath]
  first @[system;"realpath ", modulePath;{'y, " - No such file or directory"}[;modulePath]]
 };

.kuki.appendDotQ:{ x,$[x like "*.q";"";".q"] };

.kuki.importModule:{[modulePath]
  realPath: .kuki.getRealPath modulePath;
  if[realPath in .kuki.importedModules;:(::)]
  system"l ", realPath;
  .kuki.importedModules,:realPath;
 };

.kuki.importLocal:{[path;module]
  if[0=count path;path:getenv`PWD;path,:$[path like "/src";"";"/src"]];
  modulePath: .kuki.joinPath[path;.kuki.appendDotQ module];
  .kuki.importModule modulePath
 };

.kuki.importGlobal:{[module]
  subPaths: "/" vs module;
  moduleName: `$first subPaths;
  if[not moduleName in key .kuki.index; '"No module named - ", string moduleName];
  path: .kuki.joinPath[.kuki.rootDir;(first subPaths;.kuki.index[`file;`version];"src"),(-1_ 1_subPaths), enlist .kuki.appendDotQ last subPaths];
  .kuki.importModule path
 };

// format - import {"moduleName/[folder/]/module"}
// module doesn't include .q
import:{[moduleFunc]
  module: moduleFunc[];
  path: first -3#value moduleFunc;
  $[module like "./*"; .kuki.importLocal[path;module];.kuki.importGlobal[module]]
 };
