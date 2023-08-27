import{"./log.q"};
import{"./path.q"};

.ktrl.Spawn:{[profile;process;isDetached;isGlobal]
  label:(string process),".",8#string first 1?0Ng;
  cmd:" "sv(
    "ktrl";
    $[isGlobal;"--global";""];
    "--start";
    "--profile";
    string profile;
    "--process";
    string process;
    "--label";
    label
  );
  if[.kuki.kScriptType like "kest";
    .log.Warning"force to use attached mode for k test";
    isDetached:0b;
  ];
  `.ktrl.instances upsert(`$label;profile;process;0N;0N;isDetached);
  cmd:$[isDetached;
    " "sv("nohup";cmd;enlist ">";.ktrl.nohupLogDir,label;"2>&1 &");
    cmd," &"
  ];
  .log.Info"starting: ",cmd;
  system cmd;
  / allow some time for ktrl to start process
  system"sleep 0.2";
  :`$label;
 };

.ktrl.Wait:{[profile;process;isGlobal]
  cmd:" "sv(
    "ktrl";
    $[isGlobal;"--global";""];
    "--start";
    "--profile";
    string profile;
    "--process";
    string process;
    "; echo $?"
  );
  .log.Info"starting and waiting till finish: ",cmd;
  :"J"$first system cmd;
 };

.ktrl.nohupLogDir:"/tmp/",(string .z.u),"/ktrlNohupLog/";

.ktrl.MakeNohupLogDir:{[path]
  if[null path;path:.ktrl.nohupLogDir];
  .path.MkDir path;
  .ktrl.nohupLogDir:.path.ToString path;
 };

.ktrl.instances:1!flip`label`profile`process`pid`port`isDetached!"SSSJJB"$\:();

.ktrl.Kill:{[label]
  pid:.ktrl.GetPid label;
  if[not null pid;
    .log.Info "killing ",(string label);
    system"kill ",(string pid);
  ];
  if[null .ktrl.GetPid label;
    .ktrl.instances:.ktrl.instances _ label;
  ];
 };

.ktrl.ForceKill:{[label]
  pid:.ktrl.GetPid label;
  if[not null pid;
    .log.Info "killing ",(string label);
    system"kill -9 ",(string pid);
  ];
  if[null .ktrl.GetPid label;
    .ktrl.instances:.ktrl.instances _ label;
  ];
 };

.ktrl.KillAttached:{
  labels:exec label from .ktrl.instances where not isDetached;
  .ktrl.ForceKill each labels
 };

.ktrl.Interrupt:{[label]
  pid:.ktrl.GetPid label;
  .log.Info "interrupting ",(string label);
  system"kill -2 ",(string pid);
 };

.ktrl.IsRunning:{[label]
  pid:.ktrl.GetPid label;
  $[null pid;0b;1b]
 };

.ktrl.GetPid:{[label]
  pid:first @[
    "J"$first system@;
    "ps -efu | grep ' ktrl-",(string label),"' | grep -v grep | awk '{print $2}'";
    0N
  ];
  `.ktrl.instances upsert `label`pid!(label;pid);
  pid
 };

.ktrl.GetPort:{[label]
  pid:.ktrl.GetPid[label];
  port:.ktrl.instances[label;`port];
  if[null port;
    port:first "J"$last ":" vs first -2#" "vs last system"lsof -Pa -p ",(string pid)," -i";
  ];
  `.ktrl.instances upsert `label`port!(label;port);
  port
 };

.ktrl.ListInstances:{
  .ktrl.instances
 };
