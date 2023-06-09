from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, BIGINT
from app.src.base import Base


class Disk(Base):
    __tablename__ = "disks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    size = Column(BIGINT)
    filesystem = Column(String)
    mountpoint = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
