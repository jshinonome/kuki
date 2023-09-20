.kest.BeforeAll{
  .kuki.debug:1b;
 };

.kest.Test["import non exist local file";{
  .kest.ToThrowAs[(import;{"./dummy.q"});"* No such file or directory*"]
 }];

.kest.Test["import non exist package file";{
  .kest.ToThrowAs[(import;{"dummy/dummy.q"});"*cannot find pkg named - dummy*"]
 }];

.kest.Test["import non exist scope package file";{
  .kest.ToThrowAs[(import;{"@dummy/dummy/dummy.q"});"*cannot find pkg named - @dummy/dummy*"]
 }];
