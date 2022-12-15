#!/bin/bash
set -o errexit -o nounset -o pipefail

dockerfile_dir=${1:-''}
workdir=$(realpath "${2:-$dockerfile_dir/workdir}")

if [[ -z "$dockerfile_dir" ]]; then
    echo "usage: $0 dockerfile_dir [workdir]" >&2
    exit 1
fi

mapfile -t buildargs < <(
    jq -r < "$workdir/env.json" '.[] | "\(.name) \(.value)"' |
    while read -r name value; do
        printf "%q\n" --build-arg "$name=$value"
    done
)

venv/bin/cachitool apply-configs --from-output-dir "$workdir" --to-dir "$dockerfile_dir"

imagename=cachi2-$(basename "$dockerfile_dir")

set -x

podman build "$dockerfile_dir" \
    --tag "$imagename" \
    --volume "$workdir:$workdir:ro,Z" \
    "${buildargs[@]}"

podman run --rm -ti "$imagename"
