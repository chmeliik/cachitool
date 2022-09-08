from pathlib import Path

from cachitool.models.input import PipPkgSpec
from cachitool.models.output import ConfigFile, EnvVar, Output, ResolvedPackage, ResolvedDep
from cachitool.pkg_managers.pip.fetch import resolve_pip as _resolve_pip
from cachitool.pkg_managers.pip.offline import sync_repo, update_req_file


def resolve_pip(pkg_specs: list[PipPkgSpec], workdir: Path) -> Output:
    resolved = [
        _resolve_pip(pkg.path, workdir, pkg.requirements_files, pkg.requirements_build_files)
        for pkg in pkg_specs
    ]

    local_index = workdir / "piprepo"
    local_index_url = sync_repo(workdir / "deps" / "pip", local_index)

    packages = []

    for pkg, info in zip(pkg_specs, resolved):
        reqfile_paths = [Path(p) for p in info["requirements"]]
        config_files = [
            ConfigFile(content=content, relpath=reqfile_path.relative_to(pkg.path))
            for reqfile_path in reqfile_paths
            if (content := update_req_file(reqfile_path, local_index)) is not None
        ]

        deps = [ResolvedDep.parse_obj(dep) for dep in info["dependencies"]]

        resolved_pkg = ResolvedPackage(
            type="pip",
            path=pkg.path,
            dependencies=deps,
            config_files=config_files
        )
        packages.append(resolved_pkg)

    return Output(
        packages=packages,
        env_vars=[
            EnvVar(name="PIP_INDEX_URL", value=local_index_url),
        ]
    )
