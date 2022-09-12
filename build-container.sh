#!/bin/bash
set -o errexit -o nounset -o pipefail

dockerfile_dir=${1:-''}
workdir=${2:-$dockerfile_dir/workdir}

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

find "$workdir/config-files" -type f | while read -r f; do
    original_path=$(realpath "$f" --relative-base "$workdir/config-files")
    echo "Copying config file to $original_path"
    cp "$f" "$original_path"
done

imagename=cachi2-$(basename "$dockerfile_dir")
piprepo_path=$(realpath "$workdir/piprepo")

set -x

podman build "$dockerfile_dir" \
    --tag "$imagename" \
    --volume "$piprepo_path:$piprepo_path:ro,Z" \
    "${buildargs[@]}"

podman run --rm -ti "$imagename"
