import {"../../kuki/q/timer.q"};

.kest.AfterEach{
  delete from `.tmp;
 };

.kest.Test["execute 1 time";{
  f:{.tmp.n:1};
  description:"exec 1 time";
  .timer.AddJob[(f;());.z.P;.z.P+100*.timer.Milliseconds;50*.timer.Milliseconds;description];
  .timer.tick[];
  job:first .timer.GetJobsByDescription[description];
  .kest.Match[1;.tmp.n];
  .kest.Assert[job`isActive]
 }];

.kest.Test["execute at least 1 time and deactivate";{
  description:"exec 1 at least time";
  .timer.AddJob[".tmp.n:2";.z.P;.z.P;50*.timer.Milliseconds;description];
  system"sleep 0.001";
  .timer.tick[];
  .kest.Match[2;.tmp.n];
  .kest.Assert[not first exec isActive from .timer.GetJobsByDescription[description]]
 }];

.kest.Test["execute at least 1 time and deactivate by adding job at time";{
  f:{.tmp.n:3};
  description:"add job at time";
  .timer.AddJobAtTime[(f;());.z.P+1*.timer.Milliseconds;description];
  .timer.tick[];
  // jot is started yet
  .kest.ToThrow[(value;`.tmp.n);".tmp.n"];
  system"sleep 0.001";
  .timer.tick[];
  .kest.Match[3;.tmp.n];
  .kest.Assert[not first exec isActive from .timer.GetJobsByDescription[description]]
 }];


.kest.Test["schedule next time";{
  f:{.tmp.n:4};
  description:"schedule next time";
  .timer.AddJob[(f;());.z.P;.z.P+2*.timer.Second;.timer.Second;description];
  job:first .timer.GetJobsByDescription[description];
  .kest.Assert[job[`nextTime] within .z.P-(100*.timer.Milliseconds;0D)];
  .timer.tick[];
  job:first .timer.GetJobsByDescription[description];
  .kest.Assert[job[`nextTime] within .z.P+(900*.timer.Milliseconds;.timer.Second)];
  .kest.Assert[job[`lastTime] within .z.P-(100*.timer.Milliseconds;0D)];
  .kest.Match[4;.tmp.n];
  .kest.Assert[job`isActive]
 }];

.kest.Test["clear deactivate job";{
  description:"get cleared";
  .timer.AddJob[".tmp.n:5";.z.P;.z.P;50*.timer.Milliseconds;description];
  system"sleep 0.001";
  .timer.tick[];
  .kest.Match[5;.tmp.n];
  .timer.Clear[];
  .kest.Match[0;count .timer.GetJobsByDescription[description]]
 }];

.kest.Test["execute after 1 ms";{
  f:{.tmp.n:6};
  description:"execute after 1 ms";
  .timer.AddJobAfter[(f;());1*.timer.Milliseconds;description];
  .timer.tick[];
  // jot is started yet
  .kest.ToThrow[(value;`.tmp.n);".tmp.n"];
  system"sleep 0.001";
  .timer.tick[];
  .kest.Match[6;.tmp.n];
  .kest.Assert[not first exec isActive from .timer.GetJobsByDescription[description]]
 }];
