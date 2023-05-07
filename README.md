## Kdb Ultimate pacKage Installer

- use the same registry site as the npm
- use file `$HOME/.kukirc.json` to configure local registry site and token
- default local repo: `$HOME/kuki`, use environment variable `KUKIPATH` to overwrite local repo
- `kuki.json` to maintain package dependencies
- `kuki_index.json` to maintain indices of all required packages. For a version conflict:
  - it will use dependency version if it is a dependency
  - latest version if it is not a dependency

### Command: kuki

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

### Command: krun
