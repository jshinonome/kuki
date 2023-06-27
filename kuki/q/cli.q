/ command line interface
.cli.options: enlist `name`dataType`defaultValue`description!(`help;`boolean;(::);"show this help message and exit");

.cli.ignores:();

.cli.name:"";

.cli.SetName:{.cli.name:x};

.cli.add:{[name;dataType;defaultValue;description]
  defaultTypedValue: .[$;(dataType;defaultValue);{'" " sv ("failed to cast default value of";x;"-";y)}[string name]];
  .cli.options,:(name;dataType;defaultTypedValue;description);
 };

.cli.parseArgs:{[params]
  options:.Q.opt $[all 10h=type each (),params;params;.z.x];
  selectionNames:exec name from .cli.options where dataType=`selection;
  defaults:exec name!defaultValue from .cli.options where name<>`help;
  defaults:@[defaults;selectionNames;first];
  args: .Q.def[defaults] options;
  boolOptions: key[options] inter exec name from .cli.options where -1h=type each defaultValue;
  if[count boolOptions;args:@[args;boolOptions;:;1b]];
  args:.cli.ignores _ args;
  if[any fails:not args[selectionNames]in'exec defaultValue from .cli.options where dataType=`selection;
    '"Invalid selection options - ",( "," sv string selectionNames where fails)
  ];
  stringOptions: key[options] inter exec name from .cli.options where dataType=`string;
  if[count stringOptions;
    args:@[args;stringOptions;string];
  ];
  :args
 };

.cli.Parse:{[params]
  args:.cli.parseArgs params;
  if[`help in key args;.cli.printHelp[];exit 0];
  :.cli.args:args
 };

.cli.printHelp:{
  -1 .cli.name;
  -1 "";
  options:select from .cli.options where not name in .cli.ignores;
  fixedWidth: 2+max exec count each string name from options;
  -1 ((fixedWidth+3)$"options"),("type       "),"description";
  print: {[fixedWidth;name;dataType;defaultValue;description]
    $[dataType=`selection;
      -1 ("  -",fixedWidth$string name),(10$string dataType)," (",("," sv string defaultValue),"), ",description;
      -1 ("  -",fixedWidth$string name),(10$string dataType)," ",description
    ]
  };
  (print[fixedWidth] .) each 1_flip options[`name`dataType`defaultValue`description];
 };

.cli.addList:{[name;dataType;defaultValue;description]
  .cli.add[name;dataType;(),defaultValue;description];
 };

.cli.AppendIgnores:{[ignores]
  .cli.ignores,:ignores;
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
