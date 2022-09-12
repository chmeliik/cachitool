#!/bin/bash
set -o errexit -o nounset -o pipefail

repo_path=quay-test/quay
rm -rf "$repo_path"

git clone --single-branch --filter=blob:none \
    https://github.com/quay/quay \
    "$repo_path"

pushd "$repo_path"
git checkout 9b5aa476f361d673e183fc2c50e8c5dfa1027827
popd

# futures==3.1.1 was yanked and the newer ones properly declare that they don't support python 3
sed --in-place 's/futures==3.1.1/futures==3.0.5/' "$repo_path"/requirements.txt

venv/bin/cachitool \
    --package pip:"$repo_path" \
    --output-dir quay-test/workdir
