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

[0]: https://github.com/brunoapimentel/cachi2-poc/
