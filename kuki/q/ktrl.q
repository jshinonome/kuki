.cli.String[`file;"";"entry file"];
.cli.String[`dbPath;"";"database path"];
.cli.Symbol[`kHostAlias;`;"hostname alias"];
.cli.Symbol[`kProcess;`;"process name"];
.cli.Parse[1b];

.ktrl.start:{
  if[count .cli.args`dbPath;
    system "l ", .cli.args`dbPath;
  ];
  if[count .cli.args`file;
    system "l ", .cli.args`file;
  ];
  .ktrl.process.HostAlias:(first` vs .z.h)^.cli.args`kHostAlias;
  .ktrl.process.Name:.cli.args`kProcess;
  .ktrl.process.Instance:system"p";
 };
