.timer.SetInterval: {[ms] system "t " , string ms };

.timer.Milliseconds: 0D00:00:00.001;
.timer.Second: 0D00:00:01;
.timer.Minute: 0D00:01:00;
.timer.Hour: 0D01:00:00;
.timer.Day: 0D01:00:00;

.timer.jobs: 1!
  enlist `id`function`startTime`endTime`interval`lastTime`nextTime`isActive`description`updTime!
    (0; (::); 0Np; 0Np; 0Nn; 0Np; 0Np; 0b; ""; 0Np);

.timer.AddJob: {[functionCall; startTime; endTime; interval; description]
  `.timer.jobs upsert (1 + max key .timer.jobs) , `function`startTime`endTime`interval`nextTime`isActive`description`updTime!
    (functionCall; startTime; endTime; interval; startTime; 1b; description; .z.P)
 };

.timer.AddJobAtTime: {[functionCall; startTime; description]
  `.timer.jobs upsert (1 + max key .timer.jobs) , `function`startTime`endTime`interval`nextTime`isActive`description`updTime!
    (functionCall; startTime; startTime; 0D; startTime; 1b; description; .z.P)
 };

.timer.AddJobAfter: {[functionCall; interval; description]
  time: .z.P + interval;
  `.timer.jobs upsert (1 + max key .timer.jobs) , `function`startTime`endTime`interval`nextTime`isActive`description`updTime!
    (functionCall; time; time; 0D; time; 1b; description; .z.P)
 };

.timer.GetJobs: { .timer.jobs };

.timer.GetJobsByDescription: {[pattern] select from .timer.jobs where description like pattern };

.timer.ActivateJobs: {[jobId] update isActive: 1b from `.timer.jobs where id in jobId };

.timer.DeactivateJobs: {[jobId] update isActive: 0b from `.timer.jobs where id in jobId };

.timer.ActivateJobsByDescription: {[pattern]
  update isActive: 1b from `.timer.jobs where description like pattern
 };

.timer.DeactivateJobsByDescription: {[pattern]
  update isActive: 0b from `.timer.jobs where description like pattern
 };

.timer.tick: {
  jobs: select from .timer.jobs where isActive, .z.P > nextTime;
  upsert[
    `.timer.jobs;
    select id, lastTime: .z.P, nextTime: .z.P + interval from jobs where endTime >= .z.P + interval
  ];
  upsert[
    `.timer.jobs;
    select id, lastTime: .z.P, isActive: 0b from jobs where endTime < .z.P + interval
  ];
  value each exec function from jobs
 };

.timer.Start: { .z.ts: .timer.tick };

.timer.Stop: { system "x .z.ts" };

.timer.Clear: { delete from `.timer.jobs where not isActive };
