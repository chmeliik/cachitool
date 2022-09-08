from pathlib import Path

import pydantic


class ConfigFile(pydantic.BaseModel):
    content: str
    relpath: Path  # from package root


class ResolvedDep(pydantic.BaseModel):
    type: str
    name: str
    version: str
    downloaded_path: Path


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
