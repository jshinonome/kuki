# K Ultimate pacKage Installer

A package manager for q/k — install, publish, and manage packages from a self-hosted registry.

Refer to the [wiki](https://github.com/jshinonome/kuki/wiki) for full documentation.

## Installation

```bash
pip install kuki
```

Requires Python ≥ 3.7.

## Commands

`kuki` ships with three CLI tools:

| Command | Description |
|---------|-------------|
| `kuki`  | **K Ultimate pacKage Installer** — manage q/k packages |
| `kest`  | **K tEST** — test q/k code |
| `ktrl`  | **K conTRoL** — control q/k processes |

### kuki

```bash
# Initialize a new package
kuki --init

# Search for packages
kuki -s <package>

# Install packages
kuki -i <package>
kuki -i <package>@<version>

# Install packages globally
kuki -i -g <package>

# Uninstall packages
kuki -u <package>

# Download a package tarball
kuki -d <package>

# Publish the current package
kuki -p

# Unpublish a package
kuki --unpublish <package>@<version>

# Roll up version (patch, minor, major)
kuki -v patch

# Configure registry settings
kuki -c token=<token>
kuki -c registry=<url> --scope=<scope>

# Login to registry
kuki --login

# Use --insecure to disable TLS certificate verification
kuki -i <package> --insecure
```

### kest

```bash
# Initialize kest.json
kest -init

# Run tests (passes arguments through to q)
kest <args>
```

### ktrl

```bash
# List all profiles or processes
ktrl -l profile
ktrl -l process

# Configure a profile or process
ktrl -c --profile <name>
ktrl -c --process <name>

# Start a process with a profile
ktrl -s --profile <name> --process <name>

# Start in global mode
ktrl -s -g --profile <name> --process <name>

# Start in debug mode
ktrl -s --profile <name> --process <name> --debug
```

## Configuration

kuki stores configuration in `~/kuki/_config/kukirc.json` (or `$KUKIPATH/_config/kukirc.json` if `KUKIPATH` is set).

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KUKIPATH` | Root directory for kuki data (cache, config, packages) | `~/kuki` |
| `KUKIREGISTRY` | Default package registry URL | _(none)_ |

### Registry

Configure a registry before publishing or installing packages:

```bash
# Via environment variable
export KUKIREGISTRY=https://my-registry.example.com/

# Or via kuki config
kuki -c registry=https://my-registry.example.com
kuki --login
```

Scoped registries can be configured for different package scopes:

```bash
kuki -c registry=https://my-registry.example.com --scope=my-scope
kuki -c token=<token> --scope=my-scope
```

## License

[Apache-2.0](LICENSE)
