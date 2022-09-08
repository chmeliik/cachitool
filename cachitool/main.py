#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import TypedDict, TypeVar

from cachitool.models.input import PkgSpec, PipPkgSpec, make_package_spec
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


def resolve_pip(pkg: PipPkgSpec, workdir: Path) -> None:
    info = pip.resolve_pip(
        pkg.path, workdir, pkg.requirements_files, pkg.requirements_build_files
    )
    repo_dir = workdir / "piprepo"
    pip.sync_repo(workdir / "deps" / "pip", repo_dir)
    for reqfile in info["requirements"]:
        pip.modify_req_file(reqfile, repo_dir)

    import pprint
    pprint.pprint(info)


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

    for pkg in cli_args["packages"]:
        if isinstance(pkg, PipPkgSpec):
            resolve_pip(pkg, workdir)
        else:
            raise NotImplementedError(pkg.type)


if __name__ == "__main__":
    main()
