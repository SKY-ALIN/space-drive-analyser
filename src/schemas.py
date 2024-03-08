from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PlayerSchema(BaseModel):
    id: int
    ip: str
    name: str


class GameSchema(BaseModel):
    id: int
    datetime: datetime
    seed: int
    players: list[PlayerSchema]
    winner: PlayerSchema | None


class BarrierSchema(BaseModel):
    x: float
    y: float
    r: float


class MapSchema(BaseModel):
    width: float
    height: float
    seed: int
    barriers: list[BarrierSchema]


class PlayerObjectSchema(BaseModel):
    object: Literal['player']
    id: int
    x: float
    y: float
    r: float
    direction: float


class MissileObjectSchema(BaseModel):
    object: Literal['missile']
    id: int
    player_id: int
    x: float
    y: float
    direction: float


class StateSchema(BaseModel):
    time: float
    objects: list[PlayerObjectSchema | MissileObjectSchema]


class HistorySchema(BaseModel):
    map: MapSchema
    history: list[StateSchema]
    players: list[PlayerSchema]
    winner: PlayerSchema | None
