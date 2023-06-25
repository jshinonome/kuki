.kest.BeforeAll{
  .bak.log:.log;
 };

.kest.BeforeEach{
  .log:.bak.log;
 };

.kest.AfterAll{
  .log:.bak.log;
 };

.kest.Test["set log level";{
  .log.SetLogLevel`Warning;
  .kest.Match[{};.log.Debug];
  .kest.Match[{};.log.Info]
 }];

.kest.Test["set correct format type";{
  .log.SetLogFormatType`json;
  .kest.Match[`json;.log.formatType]
 }];

.kest.Test["set wrong format type";{
  .kest.ToThrow[(.log.SetLogFormatType;`dummy);"Only support log format types: `plain`json"];
 }];
