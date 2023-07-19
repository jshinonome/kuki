.cli.String[`file;"";"entry file"];
.cli.String[`dbPath;"";"database path"];
.cli.Parse[1b];

if[count .cli.args`dbPath;
  system "l ", .cli.args`dbPath;
 ];

if[count .cli.args`file;
  system "l ", .cli.args`file;
 ];
