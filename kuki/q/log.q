// https://docs.python.org/3/library/logging.html
.log.level:`info;
.log.formatType:`plain;
.log.stdHandle:1;
.log.errHandle:2;
.log.temporalShortcut:`.z.Z;
.log.jsonHeader:()!();

.log.json:{[handle;level;msgs]
  msg:$[0h=type msgs;" " sv .log.toString each msgs;.log.toString msgs];
  (neg handle) .j.j .log.jsonHeader, `level`timestamp`message!(trim(level);value .log.temporalShortcut;msg);
 };

.log.header:{[level]
  (string value .log.temporalShortcut), " ", level, " "
 };

.log.plain:{[handle;level;msgs]
  msg:$[0h=type msgs;" " sv .log.toString each msgs;.log.toString msgs];
  (neg handle) .log.header[level], msg;
 };

.log.log:{[level;msgs]
  handle:$[level~"ERROR";.log.errHandle;.log.stdHandle];
  .log[.log.formatType][handle;level;msgs];
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
  system"c ", " " sv string $[-6 -6h~type each consoleSize;consoleSize;0 0i] | system"c";
 };

.log.SetConsoleSize[25 320i];

.log.SetDatetimeShortcut:{[shortcut]
  shortcuts: `.z.T`.z.t`.z.Z`.z.z`.z.P`.z.p;
  if[not shortcut in shortcuts;'"Only support temporal types: ", -3!shortcuts];
  .log.temporalShortcut:shortcut;
 };

.log.SetLogFormatType:{[formatType]
  formatTypes: `plain`json;
  if[not formatType in formatTypes;'"Only support temporal types: ", -3!formatTypes];
  .log.formatType:formatType;
 };

.log.SetJsonHeader:{[header]
  if[not 11h=type key header;'"Only allow symbol as json header key: ", -3!header];
  .log.jsonHeader:header;
 };

.log.toString:{[msg]$[type[msg] in -10 10h;msg;-3!msg]};
