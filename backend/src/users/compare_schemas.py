from typing import Literal

from pydantic import BaseModel

from titles.schemas import TitleRead
from .schemas import UserRead


CompareBucket = Literal["both_completed", "only_me", "only_them", "both_other"]


class LibraryCompareSide(BaseModel):
    status: str | None = None
    score: float | None = None
    user_title_id: int | None = None


class LibraryCompareItem(BaseModel):
    title: TitleRead
    me: LibraryCompareSide
    them: LibraryCompareSide


class LibraryCompareCounts(BaseModel):
    both_completed: int = 0
    only_me: int = 0
    only_them: int = 0
    both_other: int = 0


class LibraryCompareResponse(BaseModel):
    other_user: UserRead
    counts: LibraryCompareCounts
    bucket: CompareBucket
    items: list[LibraryCompareItem]
