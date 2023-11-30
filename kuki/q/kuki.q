.kuki.debug: 0b;

.kuki.importedPkgs: (""; "");

.kuki.appendSlash: { $[not "/" = last x; :x , "/"; x] };

.kuki.joinPath: {[path; subPaths]
  $[
    10h = type subPaths;
      .kuki.appendSlash[path] , subPaths;
      (,/) (.kuki.appendSlash each enlist[path] ,-1 _ subPaths) ,-1 # subPaths
  ]
 };

.kuki.rootDir: {
  kukiRoot: getenv `KUKIPATH;
  $[count kukiRoot; kukiRoot; .kuki.joinPath[getenv `HOME; ("kuki")]]
 }[];

.kuki.getRealPath: {[path]
  first @[system; "realpath " , path; { 'y , " No such file or directory" }[; path]]
 };

.kuki.importPkg: {[pkgPath]
  realPath: .kuki.getRealPath pkgPath;
  if[realPath in .kuki.importedPkgs;
    :(::)
  ];
  if[not realPath like "*kuki/q/*";
    -1 "\033[0;32mloading " , realPath , "\033[0;0m"
  ];
  system "l " , realPath;
  .kuki.importedPkgs,: realPath
 };

.kuki.path: { x , $[x like "*/src"; ""; "/src"] } getenv `PWD;

.kuki.SetPath: { .kuki.path: x };

.kuki.importLocal: {[path; pkg]
  if[0 = count path;
    -1 "\033[1;33minteractive mode, use PWD '" , .kuki.path , "' for relative import\033[0;0m";
    path: .kuki.path
  ];
  pkgPath: .kuki.joinPath[path; pkg];
  .kuki.importPkg pkgPath
 };

.kuki.index: .j.k (,/) @[read0; `:kuki_index.json; { "{}" }];

.kuki.importGlobal: {[pkg]
  subPaths: "/" vs pkg;
  pkgName: `$first subPaths;
  n: $[pkg like "@*"; 2; 1];
  pkgName: `$"/" sv n # subPaths;
  if[not pkgName in key .kuki.index;
    '"cannot find pkg named - " , (string pkgName)
  ];
  path: .kuki.joinPath[
    .kuki.rootDir;
    (n # subPaths) , (.kuki.index[pkgName; `version]; "src") , n _ subPaths
  ];
  .kuki.importPkg path
 };

// global import - import {"pkgName/[folder/]/pkg"}
// local import - import {"./[folder/]/pkg"}
// pkg doesn't include .q
import: {[pkgFunc]
  if[100h <> type pkgFunc;
    '"requires format {\"pkg\"} for import"
  ];
  pkg: pkgFunc[];
  filepath: first -3 # value pkgFunc;
  path: 1 _ string first ` vs hsym `$filepath;
  errHandler: {
    -2 "\033[0;31m- fail to import " , x , " at " , y;
    -2 "error - " , z , "\033[0;0m";
    exit 1
  }[pkg; filepath];
  if[.kuki.debug;
    $[any pkg like/: ("./*"; "../*"); .kuki.importLocal[path; pkg]; .kuki.importGlobal pkg];
    :(::)
  ];
  $[
    any pkg like/: ("./*"; "../*");
      .[.kuki.importLocal; (path; pkg); errHandler];
      @[.kuki.importGlobal; pkg; errHandler]
  ]
 };

import {"./log.q"};
import {"./cli.q"};
import {"./path.q"};
import {"./timer.q"};
import {"./ktrlUtil.q"};

.kuki.kScriptType: first .Q.opt[.z.x][`kScriptType];
.kuki.debug: "-debug" in .z.x;

import {"./",.kuki.kScriptType,".q"};

// trigger .kest.run here so that error is not trapped in importing
if[.kuki.kScriptType like "kest";
  .kest.start[hsym .cli.args `testRoot]
 ];

if[.kuki.kScriptType like "ktrl";
  .ktrl.start[]
 ];
