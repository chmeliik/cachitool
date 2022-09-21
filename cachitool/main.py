#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import TypedDict, TypeVar

from cachitool.models.input import PkgSpec, PipPkgSpec, make_package_spec
from cachitool.models.output import ResolvedRequest
from cachitool.paths import OutputDir
from cachitool.pkg_managers import pip


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(description="run a subcommand")

    fetch_deps_parser = subcommands.add_parser("fetch-deps")
    fetch_deps_parser.set_defaults(
        convert_fn=convert_fetch_deps_args,
        run_fn=run_fetch_deps,
    )
    add_fetch_deps_args(fetch_deps_parser)

    apply_configs_parser = subcommands.add_parser("apply-configs")
    apply_configs_parser.set_defaults(
        convert_fn=convert_apply_configs_args,
        run_fn=run_apply_configs,
    )
    add_apply_configs_args(apply_configs_parser)

    return parser


def add_fetch_deps_args(parser: argparse.ArgumentParser) -> None:
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
        "--output-dir",
        help="directory for Cachito outputs",
        default=".",
    )


def add_apply_configs_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--from-output-dir",
        help="the output directory used for a previous fetch-deps call",
        default=".",
    )
    parser.add_argument(
        "--to-dir",
        help="apply configs only to the specified directory (can be used multiple times)",
        action="append",
    )


class FetchDepsArgs(TypedDict):
    packages: list[PkgSpec]
    output_dir: OutputDir


def convert_fetch_deps_args(args: argparse.Namespace) -> FetchDepsArgs:
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
        "output_dir": OutputDir(args.output_dir),
    }


class ApplyConfigsArgs(TypedDict):
    from_output_dir: OutputDir
    to_dirs: list[Path] | None


def convert_apply_configs_args(args: argparse.Namespace) -> ApplyConfigsArgs:
    return {
        "from_output_dir": OutputDir(args.from_output_dir),
        "to_dirs": [Path(p) for p in args.to_dir] if args.to_dir else None
    }


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


def process_output(output: ResolvedRequest, output_dir: OutputDir) -> None:
    log.info("writing config files to %s", output_dir.configs_file)

    with output_dir.configs_file.open("w") as f:
        config_files = [
            {"abspath": str(pkg.abspath / cf.relpath), "content": cf.content}
            for pkg in output.packages
            for cf in pkg.config_files
        ]
        json.dump(config_files, f)

    log.info("writing environment variables to %s", output_dir.env_file)
    with output_dir.env_file.open("w") as f:
        json.dump([env_var.dict() for env_var in output.env_vars], f)


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    try:
        cli_args = args.convert_fn(args)
    except ValueError as e:
        parser.error(str(e))

    args.run_fn(cli_args)


def run_fetch_deps(cli_args: FetchDepsArgs) -> None:
    if not cli_args["packages"]:
        parser.error("no packages to process")

    output_dir = cli_args["output_dir"]

    pip_pkgs = [pkg for pkg in cli_args["packages"] if isinstance(pkg, PipPkgSpec)]
    output = pip.resolve_pip(pip_pkgs, output_dir)

    process_output(output, output_dir)


def run_apply_configs(cli_args: ApplyConfigsArgs) -> None:
    output_dir = cli_args["from_output_dir"]

    def verbose_resolve(dirpath):
        resolved = dirpath.resolve()
        if resolved != dirpath:
            log.debug("received dir: %s, resolved to: %s", dirpath, resolved)
        return resolved

    to_dirs = cli_args["to_dirs"]
    if to_dirs:
        to_dirs = [verbose_resolve(p) for p in cli_args["to_dirs"]]

    with output_dir.configs_file.open() as f:
        configs = json.load(f)

    for config_file in configs:
        abspath = Path(config_file["abspath"])
        if not to_dirs or any(abspath.is_relative_to(dirpath) for dirpath in to_dirs):
            log.info("writing %s", abspath)
            abspath.write_text(config_file["content"])
        else:
            log.debug("not writing %s (path does not match)", abspath)


if __name__ == "__main__":
    main()
