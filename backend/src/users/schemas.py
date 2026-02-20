from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileRead(UserRead):
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False


class FollowStatusResponse(BaseModel):
    is_following: bool
