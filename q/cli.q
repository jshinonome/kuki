/ command line interface
.cli.options: enlist `name`dataType`defaultValue`description!(`help;`boolean;(::);"show this help message and exit");

.cli.add:{[name;dataType;defaultValue;description]
  defaultTypedValue: .[$;(dataType;defaultValue);{'" " sv ("failed to cast default value of";x;"-";y)}[string name]];
  .cli.options,:(name;dataType;defaultTypedValue;description);
 };

.cli.parse:{[params]
  options: .Q.opt $[all 10h=type each (),params;params;.z.x];
  args: .Q.def[exec name!defaultValue from .cli.options where name<>`help] options;
  boolOptions: key[options] inter exec name from .cli.options where -1h=type each defaultValue;
  args:@[args;boolOptions;:;1b];
  if[`help in key options;
    .cli.printHelp[];
    exit 0;
  ];
  :args
 };

.cli.printHelp:{
  1 "options:\n";
  fixedWidth: 2+max exec count each string name from .cli.options;
  print: {[fixedWidth;name;description]
    1 ("-",fixedWidth$string name),description,"\n";
  };
  (print[fixedWidth] .) each 1_flip .cli.options[`name`description];
 };

.cli.addList:{[name;dataType;defaultValue;description]
  .cli.add[name;dataType;(),defaultValue;description];
 };

.cli.boolean:.cli.add[;`boolean];
.cli.float:.cli.add[;`float];
.cli.long:.cli.add[;`long];
.cli.int:.cli.add[;`int];
.cli.date:.cli.add[;`date];
.cli.datetime:.cli.add[;`datetime];
.cli.minute:.cli.add[;`minute];
.cli.second:.cli.add[;`second];
.cli.time:.cli.add[;`time];
.cli.timestamp:.cli.add[;`timestamp];
.cli.symbol:.cli.add[;`symbol];

.cli.booleans:.cli.addList[;`boolean];
.cli.floats:.cli.addList[;`float];
.cli.longs:.cli.addList[;`long];
.cli.ints:.cli.addList[;`int];
.cli.dates:.cli.addList[;`date];
.cli.datetimes:.cli.addList[;`datetime];
.cli.minutes:.cli.addList[;`minute];
.cli.seconds:.cli.addList[;`second];
.cli.times:.cli.addList[;`time];
.cli.timestamps:.cli.addList[;`timestamp];
.cli.symbols:.cli.addList[;`symbol];
