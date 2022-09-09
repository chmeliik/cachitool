import filecmp
import io
import logging
import os.path
from pathlib import Path
from typing import Iterable

import piprepo.models

from cachitool.errors import CachitoError
from cachitool.models.output import PipResolvedDep
from cachitool.pkg_managers.pip.fetch import PipRequirementsFile, get_raw_component_name


log = logging.getLogger(__name__)


def sync_repo(pip_deps: Iterable[PipResolvedDep], repo_dir: Path) -> tuple[str, Path]:
    """Move downloaded dependencies to repo_dir and build a local index.

    External dependencies will be moved repo_dir/"external" and will not be
    part of the index. They need be replaced with file:// urls in requirements
    files.

    Replace the downloaded deps with relative symlinks pointing to their new location.

    :return:
        file:// URL to local index (absolute path)
        absolute Path to dir with external deps
    """
    repo_dir = repo_dir.resolve()
    external_dir = repo_dir / "external"

    repo_dir.mkdir(parents=True, exist_ok=True)

    for dep in pip_deps:
        dep_file = dep.downloaded_path
        if dep.is_external():
            repo_file = external_dir / dep_file.name
            external_dir.mkdir(exist_ok=True)
        else:
            repo_file = repo_dir / dep_file.name

        if not repo_file.exists():
            dep_file.rename(repo_file)
        elif filecmp.cmp(dep_file, repo_file):
            dep_file.unlink()
        else:
            msg = (
                f"{repo_file.name} already exists in the local index. "
                f"{dep_file} has the same name but different content!"
            )
            raise CachitoError(msg)

        # note: relpath will usually contain ../ and will break if either of the two dirs moves
        relpath = os.path.relpath(repo_file, start=dep_file.parent)
        dep_file.symlink_to(relpath)

    with piprepo.models.LocalIndex(source=str(repo_dir), destination=str(repo_dir)):
        log.info("Created local PyPI index at %s", repo_dir)

    index_url = f"file://{repo_dir / 'simple'}/"
    return index_url, external_dir


def update_req_file(req_file_path: Path, external_deps_dir: Path) -> str | None:
    """
    Modify pip requirement file. Return content of updated file (if updates needed) or None.

    Generates and returns a configuration file representing a custom pip requirement file where the
    original URL and VCS entries are replaced with entries pointing to entries in the local index.

    :param str req_file_path: path to the requirement file
    :param Path external_deps_dir: path to the external dir in the local index
    """
    original_requirement_file = PipRequirementsFile(req_file_path)
    external_deps_dir = external_deps_dir.resolve()

    cachito_requirements = []
    differs_from_original = False

    for requirement in original_requirement_file.requirements:
        raw_component_name = get_raw_component_name(requirement)
        if raw_component_name:
            # # increase max_attempts to make sure the package upload/setup is complete
            # worker_config = get_worker_config()
            # max_attempts = worker_config.cachito_nexus_max_search_attempts
            # new_url = nexus.get_raw_component_asset_url(
            #     raw_repo_name,
            #     raw_component_name,
            #     max_attempts=max_attempts,
            #     from_nexus_hoster=False,
            # )
            # if not new_url:
            #     raise NexusError(
            #         f"Could not retrieve URL for {raw_component_name} in {raw_repo_name}. Was the "
            #         "asset uploaded?"
            #     )

            # Inject credentials
            # if "://" not in new_url:
            #     raise NexusError(f"Nexus raw resource URL: {new_url} is not a valid URL")

            # new_url = new_url.replace("://", f"://{username}:{password}@", 1)
            # requirement = requirement.copy(url=new_url)
            filename = raw_component_name.rsplit("/")[-1]
            requirement = requirement.copy(url=f"file://{external_deps_dir / filename}")
            differs_from_original = True

        cachito_requirements.append(requirement)

    if not differs_from_original:
        # No vcs or url dependencies. No need for a custom requirements file
        return None

    cachito_requirement_file = PipRequirementsFile.from_requirements_and_options(
        cachito_requirements, original_requirement_file.options
    )
    fileobj = io.StringIO()
    cachito_requirement_file.write(fileobj)
    return fileobj.getvalue()
