from io import BytesIO
from typing import Union

from pydantic import BaseModel


class File(BaseModel):
    data: BytesIO
    name: str
    mimetype: str

    class Config:
        arbitrary_types_allowed = True


class FileId(BaseModel):
    id: str


class CatId(BaseModel):
    id: Union[str, None] = None

# if __name__ == '__main__':
