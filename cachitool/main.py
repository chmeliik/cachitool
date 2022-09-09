#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import TypedDict, TypeVar

from cachitool.models.input import PkgSpec, PipPkgSpec, make_package_spec
from cachitool.models.output import ResolvedRequest
from cachitool.pkg_managers import pip


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    pkg_exclusive = parser.add_mutually_exclusive_group()
    pkg_exclusive.add_argument(
        "--package",
        help="specify a package as type[:path] or a JSON object",
        action="append",
        default=[],
    )
    pkg_exclusive.add_argument(
        "--packagelist",
        help="specify packages as type[:path][,type[:path]] or a JSON list",
        default="[]",
    )
    parser.add_argument(
        "--workdir",
        help="working directory for the Cachito process",
        default=".",
    )
    return parser


class CLIArgs(TypedDict):
    packages: list[PkgSpec]
    workdir: Path


T = TypeVar("T")


def maybe_load_json(cli_arg: str, raw_data: str, expect_t: type[T]) -> T | None:
    if not raw_data.lstrip().startswith(("{", "[")):
        return None

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        raise ValueError(f"{cli_arg}: looks like JSON but is not valid JSON")

    if not isinstance(data, expect_t):
        expect_t_name = expect_t.__name__
        got_t_name = type(data).__name__
        raise ValueError(f"{cli_arg}: expected {expect_t_name}, got {got_t_name}")

    return data


def convert_args(args: argparse.Namespace) -> CLIArgs:
    def parse_pkg_arg(pkg_arg: str) -> PkgSpec:
        pkg_type, _, path = pkg_arg.partition(":")
        return make_package_spec({"type": pkg_type, "path": path})

    def load_pkg(pkg_arg: str) -> PkgSpec:
        jsondata = maybe_load_json("--package", pkg_arg, dict)
        if jsondata is not None:
            return make_package_spec(jsondata)
        return parse_pkg_arg(pkg_arg)

    def load_pkg_list(pkglist_arg: str) -> list[PkgSpec]:
        jsondata = maybe_load_json("--packagelist", pkglist_arg, list)
        if jsondata is not None:
            return [make_package_spec(pkg) for pkg in jsondata]
        pkg_args = map(str.strip, pkglist_arg.split(","))
        return [parse_pkg_arg(pkg_arg) for pkg_arg in pkg_args]

    packages = [load_pkg(pkg_arg) for pkg_arg in args.package]
    packagelist = load_pkg_list(args.packagelist)

    return {
        "packages": packages or packagelist,
        "workdir": Path(args.workdir),
    }


def process_output(output: ResolvedRequest, workdir: Path) -> None:
    for pkg in output.packages:
        for config_file in pkg.config_files:
            path = pkg.path / config_file.relpath
            log.info("modifying %s", path)
            path.write_text(config_file.content)

    env_file = workdir / "env.json"
    log.info("writing environment variables to %s", env_file)
    with env_file.open("w") as f:
        json.dump([env_var.dict() for env_var in output.env_vars], f)


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    try:
        cli_args = convert_args(args)
    except ValueError as e:
        parser.error(str(e))

    if not cli_args["packages"]:
        parser.error("no packages to process")

    workdir = cli_args["workdir"]

    pip_pkgs = [pkg for pkg in cli_args["packages"] if isinstance(pkg, PipPkgSpec)]
    output = pip.resolve_pip(pip_pkgs, workdir)

    process_output(output, workdir)


if __name__ == "__main__":
    main()
