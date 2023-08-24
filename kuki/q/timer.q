.timer.SetInterval:{[ms]
  system"t ",string ms
 };

.timer.Milliseconds:0D00:00:00.001;
.timer.Second:0D00:00:01;
.timer.Minute:0D00:01:00;
.timer.Hour:0D01:00:00;
.timer.Day:0D01:00:00;

.timer.jobs:1!enlist
  `id`function`startTime`endTime`interval`lastTime`nextTime`isActive`description`upd!
  (0; (::);    0Np;  0Np;0Nn;     0Np; 0Np; 0b;      "";         0Np);

.timer.AddJobs:{[function;startTime;endTime;interval;description]
  `.timer.jobs upsert (1+max key .timer.jobs),
    `function`startTime`endTime`interval`nextTime`isActive`description`upd!
    (function;startTime;endTime;interval;startTime+interval;1b;description;.z.P)
 };

.timer.GetJobs:{
  .timer.jobs
 };

.timer.GetJobsByDescription:{[pattern]
  select from .timer.jobs where description like pattern
 };

.timer.ActivateJobs:{[jobId]
  update isActivate:1b from `.timer.jobs where id in jobId
 };

.timer.DeactivateJobs:{[jobId]
  update isActivate:0b from `.timer.jobs where id in jobId
 };

.timer.ActivateJobsByDescription:{[pattern]
  update isActivate:1b from `.timer.jobs where description like pattern
 };

.timer.DeactivateJobsByDescription:{[pattern]
  update isActivate:0b from `.timer.jobs where description like pattern
 };

.timer.tick:{
  jobs:select from .timer.jobs where isActive,(.z.P<endTime)|null lastTime;
  upsert[`.timer.jobs;select id,lastTime:.z.P,nextTime:.z.P+interval from jobs where endTime>=.z.P+interval];
  upsert[`.timer.jobs;select id,lastTime:.z.P,isActive:0b from jobs where endTime<.z.P+interval];
  value each exec function from jobs;
 };

.timer.Start:{
  .z.ts:.timer.tick;
 };

.timer.Stop:{
  system"x .z.ts";
 };
