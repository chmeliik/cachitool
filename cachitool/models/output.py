import urllib.parse
from pathlib import Path
from typing import Literal

import pydantic

from cachitool.models.unique import UniqueItem, make_unique


class ConfigFile(UniqueItem):
    content: str
    relpath: Path  # from package root

    def unique_by(self) -> Path:
        return self.relpath


class ResolvedDep(UniqueItem):
    type: str
    name: str
    version: str
    downloaded_path: Path

    def unique_by(self) -> tuple[str, str, str, bool]:
        return self.type, self.name, self.version, getattr(self, "dev", False)


class PipResolvedDep(ResolvedDep):
    type: Literal["pip"]
    dev: bool = False

    def is_external(self) -> bool:
        parsed_url = urllib.parse.urlparse(self.version)
        return bool(parsed_url.scheme)


class ResolvedPackage(UniqueItem):
    """Output of resolving a single package."""
    type: str
    abspath: Path
    dependencies: list[ResolvedDep]
    config_files: list[ConfigFile] = []

    def __str__(self) -> str:
        return f"type={self.type!r} abspath={self.abspath!r} dependencies=[...] config_files=[...]"

    # don't deduplicate packages, we should never resolve the same one twice
    dedupe = False

    def unique_by(self) -> tuple[str, Path]:
        return self.type, self.abspath

    @pydantic.validator("dependencies", "config_files")
    def must_be_unique(cls, v):
        return make_unique(v)


class EnvVar(UniqueItem):
    name: str
    value: str

    def unique_by(self) -> str:
        return self.name


class ResolvedRequest(pydantic.BaseModel):
    """Output of processing the whole set of packages."""
    packages: list[ResolvedPackage]
    env_vars: list[EnvVar] = []

    @pydantic.validator("packages", "env_vars")
    def must_be_unique(cls, v):
        return make_unique(v)


def merge_outputs(o1: ResolvedRequest, o2: ResolvedRequest) -> ResolvedRequest:
    return ResolvedRequest(
        packages=o1.packages + o2.packages,
        env_vars=o1.env_vars + o2.env_vars,
    )
