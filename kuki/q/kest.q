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
  if[not expect~actual
    -2 "  expect: ", -3!expect;
    -2 "  actual: ", -3!actual;
    :0b;
  ];
  1b;
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
 };

/ loop test folder and find all filename.test.q files
.kest.run:{[root]
  files: exec file from .path.Glob[root;"*test.q"];
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
 };

.kest.style:(!) . flip(
  (`red;  "\033[1;31m");
  (`blue; "\033[1;34m");
  (`cyan; "\033[1;36m");
  (`green;"\033[0;32m");
  (`reset;"\033[0;0m");
  (`bold; "\033[;1m")
 );

.kest.setStyle:{[style]
  1 .kest.style style
 };

/ -debug option
.cli.Boolean[`debug;0b;"debug mode"];
.cli.Symbol[`root;`:test;"directory that kest use to search for test files in"];
.cli.Symbol[`outputFile;`;"write test results to a file "];
.cli.Parse[];

.kest.run[.cli.args`root];
