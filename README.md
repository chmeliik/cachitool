# Cachitool

Cachi2 CLI ([another one][0]) used for testing pip offline builds.

## How to

```shell
virtualenv --python=3.10 venv
source venv/bin/activate

pip install -e .

cachitool --help
```

## Manual tests

atomic-reactor

```shell
# download deps for atomic-reactor
./runtest.sh

# block outgoing pypi.org traffic
sudo ./block_pypi.sh

# build the atomic-reactor container
./build-container.sh atomic-reactor-test

# unblock pypi.org traffic
sudo ./unblock_pypi.sh
```

quay (this one only installs deps, atomic-reactor tests the installed app as well)

```shell
./runtest-quay.sh
sudo ./block_pypi.sh
./build-container.sh quay-test
sudo ./unblock_pypi.sh
```

## CLI usage

Basic idea: specify a list of packages, either as multiple `--package` args
or a single `--packagelist` arg. Both accept either a simple string spec
(type[:path]) or JSON.

```shell
# fetch dependencies for a pip package at ./path/to/repo
cachitool --package pip:path/to/repo

# specify more complex configuration
cachitool --package '{
    "type": "pip",
    "path": "path/to/repo",
    "requirements_build_files": ["requirements-build.txt", "requirements-pip.txt"]
}'

# fetch deps for a pip package and a gomod package
cachitool --package gomod:/path/to/repo --package pip:path/to/other-repo

cachitool --packagelist gomod:/path/to/repo,pip:path/to/other-repo

cachitool --packagelist '[
    {"type": "gomod", "path": "/path/to/repo"},
    {"type": "pip", "path": "/path/to/other-repo"}
]'

# same as above but both are in the current directory
cachitool --package pip --package gomod
cachitool --packagelist pip,gomod

# specify where to put the fetched dependencies and other miscellaneous things
#   (local pip index, env vars, content manifest, config files...)
cachitool --package pip:path/to/repo --workdir ./output  # TBD rename to output-dir
```

Note: while the examples imply two different repos, it can be two subpaths in the same
repo or really any two paths at all (for most package managers, we don't even care that
it's a git repo)

Not yet implemented: fetching repos before processing the packages

Not yet implemented: other configuration

* flags that affect the whole request: gomod-vendor, cgo-disable, ...
    * should they really affect the whole request?
    * should some of them be configured in `--package` instead?
* "environment" configuration:
    * pypi proxy url
    * gomod proxy url
    * ...
    * we can support env vars / config files for this

[0]: https://github.com/brunoapimentel/cachi2-poc/
