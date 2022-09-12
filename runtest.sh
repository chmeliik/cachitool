#!/bin/bash
set -o errexit -o nounset -o pipefail

repo_dir=atomic-reactor-test/atomic-reactor
rm -rf "$repo_dir"

git clone --single-branch --filter=blob:none \
    https://github.com/containerbuildsystem/atomic-reactor.git \
    "$repo_dir"

pushd "$repo_dir"
git checkout d59e7b941aebe33cf2855483eba96dbfb2208c93
popd

venv/bin/cachitool \
    --package '{
        "type":"pip",
        "path": "'"$repo_dir"'",
        "requirements_build_files": ["requirements-build.txt", "requirements-pip.txt"]
    }' \
    --output-dir atomic-reactor-test/workdir
