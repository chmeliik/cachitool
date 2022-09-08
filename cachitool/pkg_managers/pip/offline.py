from pathlib import Path

from cachitool.pkg_managers.pip.fetch import PipRequirementsFile, get_raw_component_name


def sync_repo(pip_deps_dir: Path, repo_dir: Path) -> None:
    pass


def modify_req_file(req_file_path: Path, repo_dir: Path) -> None:
    """
    Modify pip requirement file.

    Generates and returns a configuration file representing a custom pip requirement file where the
    original URL and VCS entries are replaced with entries pointing to entries in the local index.

    :param str req_file_path: path to the requirement file
    :param Path repo_dir: path to the local index
    """
    original_requirement_file = PipRequirementsFile(req_file_path)
    absolute_repo_dir = repo_dir.resolve()

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
            requirement = requirement.copy(url=f"file://{absolute_repo_dir / filename}")
            differs_from_original = True

        cachito_requirements.append(requirement)

    if not differs_from_original:
        # No vcs or url dependencies. No need for a custom requirements file
        return

    cachito_requirement_file = PipRequirementsFile.from_requirements_and_options(
        cachito_requirements, original_requirement_file.options
    )
    cachito_requirement_file.write(req_file_path)
