from pathlib import Path
from typing import Any, Literal

import pydantic

from cachitool import util


class PkgSpec(pydantic.BaseModel, extra="forbid"):
    type: str
    path: Path

    @pydantic.validator("path")
    def normalize_path(cls, v: str | Path) -> Path:
        return util.normpath(v)


class GoPkgSpec(PkgSpec):
    type: Literal["gomod"]


class PipPkgSpec(PkgSpec):
    type: Literal["pip"]
    requirements_files: list[Path] | None = None
    requirements_build_files: list[Path] | None = None

    @pydantic.validator("requirements_files", "requirements_build_files")
    def normalize_reqfile_paths(cls, v: list[str | Path] | None) -> list[Path] | None:
        if v is None:
            return None
        return [util.normpath(p) for p in v]


def make_package_spec(data: dict[str, Any]) -> PkgSpec:
    pkg_type = data.get("type")
    match pkg_type:
        case "gomod":
            return GoPkgSpec(**data)
        case "pip":
            return PipPkgSpec(**data)
        case _:
            raise ValueError(f"unknown package type: {pkg_type}")
