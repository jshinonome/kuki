import {"../../kuki/q/timer.q"};

.kest.AfterEach{
  delete from `.tmp;
 };

.kest.Test["execute 1 time";{
  f:{.tmp.n:1};
  description:"exec 1 time";
  .timer.AddJobs[(f;());.z.P;.z.P+100*.timer.Milliseconds;50*.timer.Milliseconds;description];
  .timer.tick[];
  job:first .timer.GetJobsByDescription[description];
  .kest.Match[1;.tmp.n];
  .kest.Match[1b;job`isActive]
 }];

.kest.Test["execute at least 1 time and deactivate";{
  f:{.tmp.n:1};
  description:"exec 1 at least time";
  .timer.AddJobs[(f;());.z.P;.z.P;50*.timer.Milliseconds;description];
  system"sleep 0.001";
  .timer.tick[];
  .kest.Match[1;.tmp.n];
  .kest.Match[0b;first exec isActive from .timer.GetJobsByDescription[description]]
 }];

.kest.Test["schedule next time";{
  f:{.tmp.n:3};
  description:"schedule next time";
  .timer.AddJobs[(f;());.z.P;.z.P+2*.timer.Second;.timer.Second;description];
  job:first .timer.GetJobsByDescription[description];
  .kest.Match[1b;job[`nextTime] within .z.P+(900*.timer.Milliseconds;.timer.Second)];
  .timer.tick[];
  job:first .timer.GetJobsByDescription[description];
  .kest.Match[1b;job[`nextTime] within .z.P+(900*.timer.Milliseconds;.timer.Second)];
  .kest.Match[1b;job[`lastTime] within .z.P-(100*.timer.Milliseconds;0D)];
  .kest.Match[3;.tmp.n];
  .kest.Match[1b;job`isActive]
 }];
