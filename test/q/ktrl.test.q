import{"../../kuki/q/ktrlUtil.q"};
import{"../../kuki/q/path.q"};

.kest.BeforeAll{
  kukiPath:.path.ToString .path.GetRelativePath{"../kuki"};
  setenv[`KUKIPATH;kukiPath];
 };

.kest.AfterAll{
  system"unset KUKIPATH";
  .ktrl.KillAttached[];
 };

.kest.Test["start 5 instances";{
  labels:{.ktrl.Spawn[`q4.0;`rte;0b;1b]}each til 5;
  .ktrl.GetPid each labels;
  .ktrl.GetPort each labels;
  .kest.Assert[0<(&//).ktrl.ListInstances[][;`pid`port]];
  .kest.Assert[not any .ktrl.ListInstances[][;`isDetached]];
  .kest.Assert[5<=count .ktrl.ListInstances[]]
 }];

.kest.Test["get pid and port";{
  label:.ktrl.Spawn[`q4.0;`rte;0b;1b];
  .kest.Assert[0<.ktrl.GetPid label];
  .kest.Assert[0<.ktrl.GetPort label]
 }];

.kest.Test["fail to start";{
  label:.ktrl.Spawn[`q4.0;`nonExisting;0b;1b];
  .kest.Assert[not .ktrl.IsRunning label]
 }];

.kest.Test["wait and exit 0";{
  exitCode:.ktrl.Wait[`q4.0;`exit0;1b];
  .kest.Match[0;exitCode]
 }];

.kest.Test["wait and exit 1";{
  exitCode:.ktrl.Wait[`q4.0;`exit1;1b];
  .kest.Match[1;exitCode]
 }];
