// delightful k test
import {"./path"};

.kest.BeforeAll:{[function]
  `.kest.tests upsert enlist (.kest.currentFile;"BeforeAll";`BeforeAll;function);
 };

.kest.AfterAll:{[function]
  `.kest.tests upsert enlist (.kest.currentFile;"AfterAll";`AfterAll;function);
 };

.kest.BeforeEach:{[function]
  `.kest.tests upsert enlist (.kest.currentFile;"BeforeEach";`BeforeEach;function);
 };

.kest.AfterEach:{[function]
  `.kest.tests upsert enlist (.kest.currentFile;"AfterEach";`AfterEach;function);
 };

.kest.Test:{[description;function]
  -1 "adding test: ", description;
  if[(.kest.currentFile;description) in key .kest.tests;
    -2 "duplicate description: '", description, "' in ", -3!.kest.currentFile;
    exit 1;
  ];
  `.kest.tests upsert enlist (.kest.currentFile;description;`Test;function);
 };

.kest.ToThrow:{[functionCall;errorMsg]
  .kest.Match[errorMsg;@[value;functionCall;{x}]]
 };

.kest.Match:{[expect;actual]
  if[not expect~actual;
    -2 "  - expect: ", -3!expect;
    -2 "  - actual: ", -3!actual;
    '"not matched";
  ];
  :1b;
 };

.kest.MatchTable:{[expectTable;actualTable]

 };

.kest.MatchDict:{[expectDict;actualDict]

 };

/ output format
/ collected * items
/ PASSED
/ FAILED
/ test file name
/ ✓ description (ms)
/ ☓ description (ms)
/   - expect:
/   - actual:
.kest.outputTestResults:{
  files: exec file from .kest.testResults;

 };

.kest.tests:2!enlist`file`description`testType`function!(`:.;"";`;(::));

.kest.testResults:2!flip`file`description`result`errMsg!"S*S*"$\:();

.kest.reset:{
  .kest.tests:0#.kest.tests;
 };

.kest.loadTest:{[file]
  -1 "loading ", 1_string file;
  .kest.currentFile:file;
  system"l ", 1_string file;
  -1 "collected ",(string count select from .kest.tests where testType=`Test), " items";
 };

/ loop test folder and find all filename.test.q files
.kest.run:{[root]
  files:exec file from .path.Glob[root;"*test.q"];
  if[not null .cli.args`testFile;
    files:(),hsym .cli.args`testFile;
  ];
  $[.cli.args`debug;
    .kest.loadTest each files;
    {[file]
      .Q.trp[.kest.loadTest;file;
        {
          `kest.testResults upsert enlist (z;"";`failed;x);
          .kest.setStyle`red;
          -2 (string z), " failed with error - ", x;
          -2 "  backtrace:";
          -2 .Q.sbt y;
          .kest.setStyle`reset;
        }[;;file]
      ]}each files
  ];
  if[not .cli.args[`testPattern]~(),"*";
    -1 "apply filter by pattern:", .cli.args[`testPattern];
    .kest.tests:delete from .kest.tests where testType=`Test, not description like .cli.args`testPattern;
  ];
  files:exec distinct file from .kest.tests where testType=`Test;
  .kest.runByFile each files;
  .kest.outputTestResults[];
 };

.kest.runByFile:{
  .kest.printStyle[`yellow;"RUNS"];
  -1 " ",string x;
  .kest.tests[(x;"BeforeAll");`function][];
  .kest.runByTest[x]each exec description from .kest.tests where file=x, testType=`Test;
  .kest.tests[(x;"AfterAll");`function][];
  $[count select from .kest.testResults where file=x, result<>`passed;
      [.kest.printStyle[`red;"FAIL"];-1 " ",string x];
      [.kest.printStyle[`green;"PASS"];-1 " ",string x]
  ];
 };

.kest.runByTest:{[file;description]
  .kest.tests[(file;"BeforeEach");`function][];
  -1 (4#" "),"- ",description;
  testFunction:.kest.tests[(file;description);`function];
  result:$[
    .cli.args`debug;
      testFunction[];
      .Q.trp[testFunction;();
        {
          .kest.setStyle`red;
          -2 "'",z,"' failed with error - ",x;
          -2 "  backtrace:";
          -2 .Q.sbt y;
          .kest.setStyle`reset;
          x
        }[;;description]
      ]
  ];
  $[result~(::);
      `.kest.testResults upsert enlist (file;description;`error;"test case should return boolean not null");
    -1h<>type result;
      `.kest.testResults upsert enlist (file;description;`error;-3!result);
      `.kest.testResults upsert enlist (file;description;`failed`passed result;"")
  ];
  .kest.tests[(file;"AfterEach");`function][];
 };

.kest.style:(!) . flip(
  (`red;        "\033[0;31m");
  (`lightRed;   "\033[1;31m");
  (`blue;       "\033[0;34m");
  (`lightBlue;  "\033[1;34m");
  (`cyan;       "\033[0;36m");
  (`lightCyan;  "\033[1;36m");
  (`yellow;     "\033[1;33m");
  (`purple;     "\033[0;35m");
  (`purple;     "\033[0;35m");
  (`pink;       "\033[1;35m");
  (`green;      "\033[0;32m");
  (`lightGreen; "\033[1;32m");
  (`bold;       "\033[;1m")
 );

.kest.printStyle:{[style;msg]
  / reset style: "\033[0;0m"
  1 (.kest.style style),msg,"\033[0;0m";
 };

/ -debug option
.cli.Boolean[`debug;0b;"debug mode"];
.cli.Symbol[`testRoot;`:test;"directory that kest use to search for test files in"];
.cli.Symbol[`testOutputFile;`;"write test results to a file"];
.cli.String[`testPattern;"*";"run only tests with a name that matches the pattern"];
.cli.Symbol[`testFile;`;"run specific test file"];
.cli.Parse[];

.kest.run[hsym .cli.args`testRoot];
