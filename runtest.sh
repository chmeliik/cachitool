#!/bin/bash
set -o errexit -o nounset -o pipefail

rm -rf atomic-reactor-test/atomic-reactor

git clone --single-branch --depth 1 \
    https://github.com/containerbuildsystem/atomic-reactor.git \
    atomic-reactor-test/atomic-reactor

venv/bin/cachitool \
    --package '{
        "type":"pip",
        "path": "atomic-reactor-test/atomic-reactor",
        "requirements_build_files": ["requirements-build.txt", "requirements-pip.txt"]
    }' \
    --workdir atomic-reactor-test/workdir
