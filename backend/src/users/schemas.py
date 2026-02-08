from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None
    
    model_config = ConfigDict(from_attributes=True)
