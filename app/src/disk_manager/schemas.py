from typing import Optional
from pydantic import BaseModel


class DiskBase(BaseModel):
    name: Optional[str] = None
    size: Optional[int] = None
    filesystem: Optional[str] = None
    mountpoint: Optional[str] = None


class DiskCreate(DiskBase):
    pass


class DiskUpdate(DiskBase):
    pass


class Disk(DiskBase):
    id: int

    class Config:
        orm_mode = True
