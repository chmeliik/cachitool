from typing import Any, ClassVar, TypeVar

import pydantic


class UniqueItem(pydantic.BaseModel):
    dedupe: ClassVar[bool] = True

    def unique_by(self) -> Any:
        raise NotImplementedError


T = TypeVar("T", bound=UniqueItem)


def make_unique(items: list[T]) -> list[T]:
    by_key: dict[Any, T] = {}
    for item in items:
        key = item.unique_by()
        prev_item = by_key.get(key)

        if prev_item is None:
            by_key[key] = item
        elif not type(item).dedupe or prev_item != item:
            raise ValueError(f"conflict by {key!r}: {prev_item} X {item}")

    return list(by_key.values())
