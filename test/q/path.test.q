.kest.Test["is dir";{
  .path.IsDir .kest.startupPath
 }];

.kest.Test["is file";{
  .path.IsFile ` sv .kest.startupPath,`README.md
 }];

.kest.Test["exists";{
  .path.Exists ` sv .kest.startupPath,`README.md
 }];

.kest.Test["not exists";{
  not .path.Exists ` sv .kest.startupPath,`dummy.md
 }];

.kest.Test["walk directory";{
  .kest.Match[8;count .path.Walk "test/data"]
 }];

.kest.Test["glob directory";{
  .kest.Match[2;count .path.Glob[`:test/data;"*csv*"]]
 }];

.kest.Test["join path";{
  .kest.Match[.path.JoinPath[.path.Cwd[];"test"];.path.ToHsym .path.GetRealPath"test"]
 }];

.kest.Test["get relative path";{
  .kest.Match[.path.JoinPath[.path.Cwd[];"test/q/test"];.path.GetRelativePath{"test"}]
 }];
