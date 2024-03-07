from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from db import Base


class Player(Base):
    __tablename__ = 'players'
    __table_args__ = (
        UniqueConstraint('ip', 'name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, nullable=False)
    name = Column(String, nullable=False)


class PlayerGameLink(Base):
    __tablename__ = 'player_game_links'
    player_id = Column(ForeignKey('players.id'), primary_key=True)
    game_id = Column(ForeignKey('games.id'), primary_key=True)


class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, index=True)
    datetime = Column(DateTime, nullable=False)
    raw_data = Column(String, nullable=False)
    winner_id = Column(ForeignKey('players.id'), nullable=True)
    seed = Column(Integer, nullable=False)
