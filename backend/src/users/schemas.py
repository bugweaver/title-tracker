from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    is_private: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserProfileRead(UserRead):
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=2000)
    is_private: bool | None = None


class FollowStatusResponse(BaseModel):
    is_following: bool

