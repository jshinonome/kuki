.kuki.importedModules:("";"");

.kuki.appendSlash:{$[not "/"=last x;:x,"/";x]};

.kuki.joinPath:{[path;subPaths]
  $[10h=type subPaths;
    .kuki.appendSlash[path],subPaths;
    (,/)(.kuki.appendSlash each enlist[path],-1_subPaths),-1#subPaths
  ]
 };

.kuki.rootDir:{kukiRoot:getenv`KUKIPATH;$[count kukiRoot;kukiRoot;.kuki.joinPath[getenv`HOME;("kuki")]]}[];

.kuki.getRealPath:{[path]
  first @[system;"realpath ", path;{'y, " - No such file or directory"}[;path]]
 };

.kuki.importModule:{[modulePath]
  realPath: .kuki.getRealPath modulePath;
  if[realPath in .kuki.importedModules;:(::)]
  system"l ", realPath;
  .kuki.importedModules,:realPath;
 };

.kuki.path:{x,:$[x like "/src";"";"/src"]}getenv`PWD;

.kuki.SetPath:{.kuki.path:x};

.kuki.importLocal:{[path;module]
  if[0=count path;path:.kuki.path];
  modulePath: .kuki.joinPath[path;module];
  .kuki.importModule modulePath
 };

.kuki.index:.j.k (,/) @[read0;`:kuki_index.json;{"{}"}];

.kuki.importGlobal:{[module]
  subPaths: "/" vs module;
  moduleName: `$first subPaths;
  n:$[module like "@*";2;1];
  moduleName:`$ "/" sv n#subPaths;
  if[not moduleName in key .kuki.index; '"Cannot find module named - ", string moduleName];
  path: .kuki.joinPath[.kuki.rootDir;
    (n#subPaths),
    (.kuki.index[moduleName;`version];"src"),
    n _ subPaths
  ];
  .kuki.importModule path
 };

// global import - import {"moduleName/[folder/]/module"}
// local import - import {"./[folder/]/module"}
// module doesn't include .q
import:{[moduleFunc]
  if[100h<>type moduleFunc;'"requires format {\"module\"} for import"];
  module: moduleFunc[];
  path: first -3#value moduleFunc;
  path: 1_string first ` vs hsym `$path;
  errHandler:{'"fail to import ",x," at ",y," - ", z}[module;path];
  $[any module like/: ("./*";"../*");
      .[.kuki.importLocal;(path;module);errHandler];
      @[.kuki.importGlobal;module;errHandler]
  ]
 };

import {"./log.q"};
import {"./cli.q"};
import {"./path.q"};

.kuki.kScriptType:first .Q.opt[.z.x][`kScriptType];

import {"./",.kuki.kScriptType,".q"};

// trigger .kest.run here so that error is not trapped in importing
if[.kuki.kScriptType like "kest";
  .kest.run[hsym .cli.args`testRoot];
 ];
