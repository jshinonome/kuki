.path.ToHsym:{[path]
  $[10h=type path;hsym`$path;
    -11h=type path;hsym path;
      '"UnsupportedType"
  ]
 };

.path.ToString:{[path]
  stringPath:
    $[-11h=type path;string path;
      10h=type path;path;
        '"UnsupportedType"
    ];
  $[":"=stringPath 0;1_stringPath;stringPath]
 };

.path.IsDir:{0<type key .path.ToHsym x};

.path.IsFile:{0>type key .path.ToHsym x};

.path.Exists:{0h<>type key .path.ToHsym x};

.path.Remove:{hdel .path.ToHsym x};

.path.MkDir:{if[not .path.Exists x;system"mkdir -p " .path.ToString x]};

.path.Walk:{[path]
  path: .path.ToHsym path;
  files: paths where 0 > (type key@) each paths: .Q.dd[path] each paths: key path;
  dirs: paths where 0 < (type key@) each paths;
  :(flip `dir`file!((count files)#path;files)) uj (uj/) .z.s each dirs
 };

.path.Glob:{[path;pattern]
  :?[.path.Walk[path];enlist(like;`file;pattern);0b;()];
 };

.path.Home:{hsym `$getenv`HOME};

.path.Cwd:{hsym `$first system"pwd"};

.path.appendSlash:{[path]
  .kuki.appendSlash path
 };

// same as .kuki.getRealPath
.path.GetRealPath:{[path]
  .kuki.getRealPath .path.ToString path
 };

// same as .kuki.joinPath
.path.JoinPath:{[path;subPaths]
  path:.path.ToString path;
  subPaths:$[type[subPaths] in 0 10h;subPaths;.path.ToString each subPaths];
  .path.ToHsym .kuki.joinPath[.path.ToString path;subPaths]
 };

.path.GetRelativePath:{[pathFunc]
  targetPath: pathFunc[];
  path: first -3#value pathFunc;
  path: 1_string first ` vs hsym `$path;
  .path.JoinPath[path;targetPath]
 };
