// https://docs.python.org/3/library/logging.html
.log.level:`info;
.log.formatType:`plain;
.log.stdHandle:1;
.log.errHandle:2;
.log.temporalShortcut:`.z.Z;

.log.json:{[level;msgs]
  handle:$[level=`error;.log.errHandle;.log.stdHandle];

 };

.log.header:{[level]
  (string value .log.temporalShortcut), " ", level, " "
 };

.log.plain:{[level;msgs]
  handle:$[level~"ERROR";.log.errHandle;.log.stdHandle];
  handle .log.header[level], $[0h=type msgs;" " sv .log.toString each msgs;.log.toString msgs], "\n";
 };

.log.log:{[level;msgs]
  .log[.log.formatType][level;msgs];
 };

.log.Debug:.log.log["DEBUG"];

.log.Info:.log.log["INFO "];

.log.Warning:.log.log["WARN "];

.log.Error:.log.log["ERROR"];

.log.SetStdLogFile:{[filepath]
  h:hopen filepath;
  .log.stdHandle:h;
  .log.errHandle:h;
 };

.log.SetErrLogFile:{[filepath]
  h:hopen filepath;
  .log.errHandle:h;
 };

.log.SetConsoleSize:{[consoleSize]
  system"c ", " " sv string $[(::)~consoleSize;0 0i;consoleSize] | system"c";
 };

.log.SetConsoleSize[25 320i];

.log.SetDatetimeShortcut:{[shortcut]
  shortcuts: `.z.T`.z.t`.z.Z`.z.z`.z.P`.z.p;
  if[not shortcut in shortcuts;'"Only support temporal types: ", -3!shortcuts];
  .log.temporalShortcut:shortcut;
 };

.log.toString:{[msg]$[type[msg] in -10 10h;msg;-3!msg]};
