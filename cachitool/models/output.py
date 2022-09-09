import urllib.parse
from pathlib import Path
from typing import Literal

import pydantic


class ConfigFile(pydantic.BaseModel):
    content: str
    relpath: Path  # from package root


class ResolvedDep(pydantic.BaseModel):
    type: str
    name: str
    version: str
    downloaded_path: Path


class PipResolvedDep(ResolvedDep):
    type: Literal["pip"]

    def is_external(self) -> bool:
        parsed_url = urllib.parse.urlparse(self.version)
        return bool(parsed_url.scheme)


class ResolvedPackage(pydantic.BaseModel):
    """Output of resolving a single package."""
    type: str
    path: Path
    dependencies: list[ResolvedDep]
    config_files: list[ConfigFile] = []


class EnvVar(pydantic.BaseModel):
    name: str
    value: str


class Output(pydantic.BaseModel):
    """Output of processing the whole set of packages."""
    packages: list[ResolvedPackage]
    env_vars: list[EnvVar] = []
