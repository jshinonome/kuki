## K Ultimate pacKage Installer

- use the same registry site as the npm
- use file `$HOME/.kukirc.json` to configure local registry site and token
- default local repo: `$HOME/kuki`, use environment variable `KUKIPATH` to overwrite local repo
- `kuki.json` to maintain package dependencies
- `kuki_index.json` to maintain indices of all required packages. For a version conflict:
  - it will use dependency version if it is a dependency
  - latest version if it is not a dependency

### Command: kuki

K Ultimate pacKage Installer

#### config

use format 'field=value'

```bash
kuki --config registry=https://localhost token=some_token
```

#### init

init kuki.json for a new package

```bash
kuki --init
```

#### publish

publish current package to the registry

```bash
kuki --publish
```

#### download

download a package from the registry

```bash
kuki --download dummy
kuki --download dummy@0.0.1
```

#### install

install a package to the local repo

```bash
kuki --install dummy
kuki --install dummy@0.0.1
```

#### uninstall

uninstall a package from current working package

```bash
kuki --uninstall dummy
```

### Command: kest

K tEST CLI

#### Define Test

- `.kest.Test[description;function]`

#### Setup and Teardown

- `.kest.BeforeAll function`
- `.kest.AfterAll function`
- `.kest.BeforeEach function`
- `.kest.AfterEach function`

#### Using Matchers

- `.kest.ToThrow[functionCall;errorMsg]`
- `.kest.Match[expect;actual]`
- `.kest.MatchTable[expect;actual]`
- `.kest.MatchDict[expect;actual]`

### Command: ktrl

K conTRoL CLI

#### Init ktrl Profile

`ktrl -init [-global|mongodb] profile_name`

locations for profiles

- mongodb: stored in MongoDB
- global: `$HOME/kuki/_profile`
- local: `$PWD/profile`

#### Start Process Using ktrl Profile

`ktrl -profile [-global|mongodb] profile_name`

- with `-mongodb`, ktrl will use profiles in MongoDB
- with `-global`, ktrl will use profiles in global profile directory
- without `-global|mongodb`, ktrl will use profiles as following priorities:
  - local directory
  - global profile directory
  - MongoDB

#### Config ktrl

`ktrl -config`

Config ktrl includes MongoDB connection details, configuration file path `$HOME/kuki/_config/ktrlrc.json`
