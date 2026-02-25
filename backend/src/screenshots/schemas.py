from pydantic import BaseModel, ConfigDict


class ScreenshotRead(BaseModel):
    id: int
    url: str
    position: int

    model_config = ConfigDict(from_attributes=True)
