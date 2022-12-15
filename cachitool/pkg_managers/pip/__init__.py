from itertools import chain
from pathlib import Path

from cachitool.models.input import PipPkgSpec
from cachitool.models.output import ConfigFile, EnvVar, ResolvedRequest, ResolvedPackage, PipResolvedDep
from cachitool.paths import OutputDir
from cachitool.pkg_managers.pip.fetch import resolve_pip as _resolve_pip
from cachitool.pkg_managers.pip.offline import sync_repo, update_req_file


def resolve_pip(pkg_specs: list[PipPkgSpec], output_dir: OutputDir) -> ResolvedRequest:
    resolved = [
        _resolve_pip(pkg.path, output_dir, pkg.requirements_files, pkg.requirements_build_files)
        for pkg in pkg_specs
    ]

    packages = []

    for pkg_spec, info in zip(pkg_specs, resolved):
        resolved_pkg = ResolvedPackage(
            type="pip",
            abspath=pkg_spec.path,
            dependencies=[
                PipResolvedDep.parse_obj(dep) for dep in info["dependencies"]
            ],
        )
        packages.append(resolved_pkg)

    all_deps = chain.from_iterable(pkg.dependencies for pkg in packages)
    local_index_url, external_dir = sync_repo(all_deps, output_dir.pip_local_index)

    for pkg, info in zip(packages, resolved):
        reqfile_paths = [Path(p) for p in info["requirements"]]
        config_files = [
            ConfigFile(content=content, relpath=reqfile_path.relative_to(pkg.abspath))
            for reqfile_path in reqfile_paths
            if (content := update_req_file(reqfile_path, external_dir)) is not None
        ]
        pkg.config_files = config_files

    return ResolvedRequest(
        packages=packages,
        env_vars=[
            EnvVar(name="PIP_INDEX_URL", value=local_index_url),
        ]
    )
