.kest.Test["import non exist local file";{
  .kest.ToThrowAs[(import;{"./dummy.q"});"* No such file or directory"]
 }];

.kest.Test["import non exist package file";{
  .kest.ToThrowAs[(import;{"dummy/dummy.q"});"* Cannot find module named - dummy"]
 }];

.kest.Test["import non exist scope package file";{
  .kest.ToThrowAs[(import;{"@dummy/dummy/dummy.q"});"* Cannot find module named - @dummy/dummy"]
 }];
