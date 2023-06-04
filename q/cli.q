/ command line interface
.cli.options: enlist `name`dataType`defaultValue`description!(`help;`boolean;(::);"show this help message and exit");

.cli.ignores:();

.cli.add:{[name;dataType;defaultValue;description]
  defaultTypedValue: .[$;(dataType;defaultValue);{'" " sv ("failed to cast default value of";x;"-";y)}[string name]];
  .cli.options,:(name;dataType;defaultTypedValue;description);
 };

.cli.Parse:{[params]
  options:.Q.opt $[all 10h=type each (),params;params;.z.x];
  selectionNames:exec name from .cli.options where dataType=`selection;
  defaults:(exec name!defaultValue from .cli.options where name<>`help, dataType<>`selection),
    selectionNames!(count selectionNames)#`;
  args: .Q.def[defaults] options;
  boolOptions: key[options] inter exec name from .cli.options where -1h=type each defaultValue;
  if[count boolOptions;args:@[args;boolOptions;:;1b]];
  args:.cli.ignores _ args;
  if[any fails:not args[selectionNames]in'exec defaultValue from .cli.options where dataType=`selection;
    '"Invalid selection options - ",( "," sv string selectionNames where fails)
  ];
  if[`help in key options;.cli.printHelp[];exit 0];
  :args
 };

.cli.printHelp:{
  -1 "options:";
  fixedWidth: 2+max exec count each string name from .cli.options;
  print: {[fixedWidth;name;dataType;defaultValue;description]
    $[dataType=`selection;
      -1 ("-",fixedWidth$string name),(10$string dataType),"(",("," sv string defaultValue),"), ",description;
      -1 ("-",fixedWidth$string name),(10$string dataType),", ",description
    ]
  };
  (print[fixedWidth] .) each 1_flip .cli.options[`name`dataType`defaultValue`description];
 };

.cli.addList:{[name;dataType;defaultValue;description]
  .cli.add[name;dataType;(),defaultValue;description];
 };

.cli.SetIgnore:{[ignores]
  .cli.ignores:ignores;
 };

.cli.Selection:{[name;selections;description]
  defaultTypedValue: .[$;(`symbol;(),selections);{'" " sv ("failed to cast default value of";x;"-";y)}[string name]];
  .cli.options,:(name;`selection;defaultTypedValue;description);
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
