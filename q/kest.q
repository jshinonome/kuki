// delightful k test
import {"./path"};

.kest.BeforeAll:{[function]
  level: last .kest.tests`level;
  `.kest.tests upsert enlist ("";`BeforeAll;level;(::));
 };

.kest.AfterAll:{[function]
  level: last .kest.tests`level;
  `.kest.tests upsert enlist ("";`AfterAll;level;(::));
 };

.kest.BeforeEach:{[function]
  level: last .kest.tests`level;
  `.kest.tests upsert enlist ("";`BeforeEach;level;(::));
 };

.kest.AfterEach:{[function]
  level: last .kest.tests`level;
  `.kest.tests upsert enlist ("";`AfterEach;level;(::));
 };

.kest.Test:{[description;function]
  level: last .kest.tests`level;
  `.kest.tests upsert enlist (description;`Test;level;function);
 };

.kest.Describe:{[description;function]
  level: 1+last .kest.tests`level;
  `.kest.tests upsert enlist (description;`DescribeEntry;level;function);
 };

.kest.ToThrow:{[function;errorMsg]

 };

.kest.Match:{[expect;actual]

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

-1 "\033[0;32m✓";
-1 "\033[1;31m☓";

.kest.tests:flip`description`testType`level`function!"*SJ*"$\:();

.kest.testFiles:();

/ loop test folder and find all filename.test.q files
.kest.run:{

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
  1 .kest.style
 };

/ -debug option
