/ command line interface
.cli.options: flip`name`dataType`defaultValue`description!flip(
  (`help; `boolean;(::);"show this help message and exit");
  (`pHelp;`boolean;(::);"show process options and exit")
 );

.cli.name:"";

.cli.SetName:{.cli.name:x};

.cli.add:{[name;dataType;defaultValue;description]
  defaultTypedValue: .[$;(dataType;defaultValue);{'" " sv ("failed to cast default value of";x;"-";y)}[string name]];
  .cli.options,:(name;dataType;defaultTypedValue;description);
 };

.cli.parseArgs:{[params]
  options:.Q.opt $[all 10h=type each (),params;params;.z.x];
  selectionNames:exec name from .cli.options where dataType=`selection;
  defaults:exec name!defaultValue from .cli.options where not name in `help`pHelp;
  defaults:@[defaults;selectionNames;first];
  args: .Q.def[defaults] options;
  boolOptions: key[options] inter exec name from .cli.options where -1h=type each defaultValue;
  if[count boolOptions;args:@[args;boolOptions;:;1b]];
  args:(key[args] inter .cli.options`name)#args;
  / allow mixed type values
  args:((enlist `)!enlist (::)),args;
  if[any fails:not args[selectionNames]in'exec defaultValue from .cli.options where dataType=`selection;
    '"Invalid selection options - ",( "," sv string selectionNames where fails)
  ];
  stringOptions: exec name from .cli.options where dataType=`string;
  if[count stringOptions;
    args:@[args;stringOptions;string];
  ];
  args:` _ args;
  :args;
 };

.cli.Parse:{[skipHelp]
  args:.cli.parseArgs[];
  skipHelp:$[null skipHelp;0b;skipHelp];
  if[not[skipHelp] & `help in key args;.cli.printHelp[];exit 0];
  if[not[skipHelp] &`pHelp in key args;.cli.printProcessHelp[];exit 0];
  .cli.args:args;
  :.cli.Args:((key args) where (key args) like "k[A-Z]*")_args;
 };

.cli.printHelp:{
  -1 .cli.name;
  -1 "";
  fixedWidth: 2+max exec count each string name from .cli.options;
  -1 ((fixedWidth+3)$"options"),("type       "),"description";
  print: {[fixedWidth;name;dataType;defaultValue;description]
    $[dataType=`selection;
      -1 ("  -",fixedWidth$string name),(10$string dataType)," ",description," (",("," sv string defaultValue),")";
      -1 ("  -",fixedWidth$string name),(10$string dataType)," ",description
    ]
  };
  (print[fixedWidth] .) each flip .cli.options[`name`dataType`defaultValue`description];
 };

.cli.addList:{[name;dataType;defaultValue;description]
  .cli.add[name;dataType;(),defaultValue;description];
 };

.cli.Selection:{[name;selections;description]
  .cli.options,:(name;`selection;(),selections;description);
 };

.cli.String:{[name;defaultValue;description]
  if[not type[defaultValue]in -10 10h;'"require char or chars data type for ",string name];
  .cli.options,:(name;`string;`$defaultValue;description);
 };

.cli.Boolean:.cli.add[;`boolean];
.cli.Float:.cli.add[;`float];
.cli.Long:.cli.add[;`long];
.cli.Int:.cli.add[;`int];
.cli.Date:.cli.add[;`date];
.cli.Datetime:.cli.add[;`datetime];
.cli.Minute:.cli.add[;`minute];
.cli.Second:.cli.add[;`second];
.cli.Time:.cli.add[;`time];
.cli.Timestamp:.cli.add[;`timestamp];
.cli.Symbol:.cli.add[;`symbol];

.cli.Booleans:.cli.addList[;`boolean];
.cli.Floats:.cli.addList[;`float];
.cli.Longs:.cli.addList[;`long];
.cli.Ints:.cli.addList[;`int];
.cli.Dates:.cli.addList[;`date];
.cli.Datetimes:.cli.addList[;`datetime];
.cli.Minutes:.cli.addList[;`minute];
.cli.Seconds:.cli.addList[;`second];
.cli.Times:.cli.addList[;`time];
.cli.Timestamps:.cli.addList[;`timestamp];
.cli.Symbols:.cli.addList[;`symbol];

.cli.printProcessHelp:{
  -1 each (
    "options      default   description";
    "  -b                   block write-access except handle 0";
    "  -c         25 80     console maximum rows and columns";
    "  -e         0         error-trapping mode(0:none, 1:suspend, 2:dump)";
    "  -E         0         TLS server mode(0:plain, 1:mixed, 2:tls)";
    "  -g         0         garbage collection mode(0:deferred, 1:immediate)";
    "  -o         0         offset from UTC in hours";
    "  -p                   listening port";
    "  -P         7         display precision";
    "  -q                   quiet mode";
    "  -r                   replicate from :host:port";
    "  -s         0         number of threads or processes available for parallel processing";
    "  -t         0         timer period in milliseconds";
    "  -T         0         timeout in seconds for client queries";
    "  -u                   blocks system functions and file access(1, user-password file)";
    "  -U                   sets user-password file, blocks \\x";
    "  -w         0         memory limit in MB"
  )
 };
