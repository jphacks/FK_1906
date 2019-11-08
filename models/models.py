from sqlalchemy import Column, Integer, String, Text, DateTime
from models.database import Base
from datetime import datetime


class Progress(Base):
    __tablename__ = 'logcontents'
    id = Column(Integer, primary_key=True)
    movie_frames = Column(Integer)
    movie_progress = Column(Integer)
    #date = Column(DateTime, default=datetime.now())

    def __init__(self, movie_frames=None, movie_progress=None):
        self.movie_frames = movie_frames
        self.movie_progress = movie_progress

    def __repr__(self):
        return '<frames:{frames} progress:{progress}>'.format(frames = self.movie_frames, progress = self.movie_progress)
