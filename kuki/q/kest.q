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
    msg: "\n" sv (
      "  Mismatch";
      "    Expected: ", -3!expect;
      "    Received: ", -3!actual
    );
    -2 .kest.getMsgByStyle[`red;msg];
    'msg;
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
  statusByFile:exec all status=`passed by file from .kest.testResults;
  numFiles:count statusByFile;
  numPassedFiles:`long$sum statusByFile;
  -1 "test Files: ",(string numFiles)," total, ",(string numPassedFiles)," passed";
  numTests:count .kest.testResults;
  numPassedTests:`long$sum exec status=`passed from .kest.testResults;
  -1 "tests:      ",(string numTests)," total, ",(string numPassedTests)," passed";
  time:`long$(.z.P-.kest.startTime)%1e6;
  -1 "time:       ",(string time),"ms";
  if[not null .cli.args`testOutputFile;
    (hsym .cli.args[`testOutputFile]) 0: enlist .j.j (!) . flip (
      (`numFiles; numFiles);
      (`numPassedFiles; numPassedFiles);
      (`numFailedFiles; numFiles-numPassedFiles);
      (`numTests; numTests);
      (`numPassedTests; numPassedTests);
      (`numFailedTests; numTests-numPassedTests);
      (`time;time);
      (`testResults;.kest.testResults)
    );
  ];
 };

.kest.tests:2!enlist`file`description`testType`function!(`:.;"";`;(::));

.kest.testResults:2!flip`file`description`status`errMsg`time!"S*S*J"$\:();

.kest.reset:{
  .kest.tests:0#.kest.tests;
 };

.kest.loadTest:{[testFile]
  -1 "loading ", 1_string testFile;
  .kest.currentFile:testFile;
  system"l ", 1_string testFile;
  -1 "collected ",(string count select from .kest.tests where file=testFile, testType=`Test), " items\n";
 };

.kest.runByFile:{
  startTime:.z.P;
  -1 .kest.getMsgByStyle[`yellow;"RUNS"]," ",string x;
  .kest.tests[(x;"BeforeAll");`function][];
  .kest.runByTest[x]each exec description from .kest.tests where file=x, testType=`Test;
  .kest.tests[(x;"AfterAll");`function][];
  msg:" ",(string x)," (",(string `long$(.z.P-startTime)%1e6),"ms)\n";
  $[count select from .kest.testResults where file=x, status<>`passed;
      -2 .kest.getMsgByStyle[`red;"FAIL"],msg;
      -1 .kest.getMsgByStyle[`green;"PASS"],msg
  ];
 };

.kest.runByTest:{[file;description]
  startTime:.z.P;
  .kest.tests[(file;"BeforeEach");`function][];
  testFunction:.kest.tests[(file;description);`function];
  result:$[
    .cli.args`debug;
      testFunction[];
      .Q.trp[testFunction;();
        {
          if[x like "*Mismatch*";:x];
          errMsg:"\n" sv ("'",z,"' failed with error - ",x;"  backtrace:";.Q.sbt y);
          -2 .kest.getMsgByStyle[`red;errMsg];
          errMsg
        }[;;description]
      ]
  ];
  .kest.tests[(file;"AfterEach");`function][];
  usedTime:`long$(.z.P-startTime)%1e6;
  status:$[result~1b;`passed;`failed];
  errMsg:$[
    1h=type result;
      "";
    10h=type result;
      result;
    (::)~result;
      "test case should return boolean not null";
      "expect boolean not ", -3!result
  ];
  `.kest.testResults upsert enlist (file;description;status;errMsg;usedTime);
  $[status=`passed;
      -1 " " sv (.kest.getMsgByStyle[`lightGreen;"✓"];description;"(",(string usedTime),"ms)");
      -2 " " sv (.kest.getMsgByStyle[`lightRed;"✘"];description;"(",(string usedTime),"ms)")
  ];
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
  (`pink;       "\033[1;35m");
  (`green;      "\033[0;32m");
  (`lightGreen; "\033[1;32m");
  (`bold;       "\033[;1m")
 );

.kest.getMsgByStyle:{[style;msg]
  / reset style: "\033[0;;0m"
  :(.kest.style style),msg,"\033[0;0m";
 };

/ loop test folder and find all filename.test.q files
.kest.run:{[root]
  .kest.startTime:.z.P;
  files:exec file from .path.Glob[root;"*test.q"];
  if[not null .cli.args`testFile;
    files:(),hsym .cli.args`testFile;
  ];
  $[.cli.args`debug;
    .kest.loadTest each files;
    {[file]
      .Q.trp[.kest.loadTest;file;
        {
          errMsg:"\n" sv ((string z), " failed to load with error - ", x;"  backtrace:";.Q.sbt y);
          `kest.testResults upsert enlist (z;"";`failed;errMsg;0Nt);
          -2 .kest.getMsgByStyle[`red;errMsg];
          errMsg
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
  if[not .cli.args`debug;
    exit not all exec `passed=status from .kest.testResults;
  ];
 };

/ -debug option
.cli.Boolean[`debug;0b;"debug mode"];
.cli.Boolean[`init;0b;"initialize kest.json"];
.cli.Symbol[`testRoot;`:test;"directory that kest use to search for test files in"];
.cli.Symbol[`testOutputFile;`;"write test results to a file"];
.cli.String[`testPattern;"*";"run only tests with a name that matches the pattern"];
.cli.Symbol[`testFile;`;"run specific test file"];
.cli.SetName["K tEST CLI"];
.cli.Parse[];

.kest.startupPath:.path.Cwd[];
.kest.run[hsym .cli.args`testRoot];
