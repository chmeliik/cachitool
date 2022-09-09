from itertools import chain
from pathlib import Path

from cachitool.models.input import PipPkgSpec
from cachitool.models.output import ConfigFile, EnvVar, ResolvedRequest, ResolvedPackage, PipResolvedDep
from cachitool.pkg_managers.pip.fetch import resolve_pip as _resolve_pip
from cachitool.pkg_managers.pip.offline import sync_repo, update_req_file


def resolve_pip(pkg_specs: list[PipPkgSpec], workdir: Path) -> ResolvedRequest:
    resolved = [
        _resolve_pip(pkg.path, workdir, pkg.requirements_files, pkg.requirements_build_files)
        for pkg in pkg_specs
    ]

    packages = []

    for pkg, info in zip(pkg_specs, resolved):
        resolved_pkg = ResolvedPackage(
            type="pip",
            path=pkg.path,
            dependencies=[
                PipResolvedDep.parse_obj(dep) for dep in info["dependencies"]
            ],
        )
        packages.append(resolved_pkg)

    all_deps = chain.from_iterable(pkg.dependencies for pkg in packages)
    local_index = workdir / "piprepo"
    local_index_url, external_dir = sync_repo(all_deps, local_index)

    for resolved_pkg in packages:
        reqfile_paths = [Path(p) for p in info["requirements"]]
        config_files = [
            ConfigFile(content=content, relpath=reqfile_path.relative_to(pkg.path))
            for reqfile_path in reqfile_paths
            if (content := update_req_file(reqfile_path, external_dir)) is not None
        ]
        resolved_pkg.config_files = config_files

    return ResolvedRequest(
        packages=packages,
        env_vars=[
            EnvVar(name="PIP_INDEX_URL", value=local_index_url),
        ]
    )
