from datetime import datetime
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import aliased

from db import get_session
from models import Game, Player, PlayerGameLink
from schemas import GameSchema, HistorySchema

router = APIRouter(prefix='/games', tags=['Game'])


@router.get('', response_model=list[GameSchema])
async def get_games(session: AsyncSession = Depends(get_session)):
    Winner: type[Player] = aliased(Player)
    stmt = select(
        Game.id,
        Game.datetime,
        Game.seed,
        func.json_group_array(
            func.json_object(
                'id', Player.id,
                'ip', Player.ip,
                'name', Player.name,
            ),
        ).label('players'),
        func.json_object(
            'id', Winner.id,
            'ip', Winner.ip,
            'name', Winner.name,
        ).label('winner'),
    ).select_from(
        Game,
    ).join(
        PlayerGameLink,
        PlayerGameLink.game_id == Game.id,
    ).join(
        Player,
        Player.id == PlayerGameLink.player_id,
    ).join(
        Winner,
        Winner.id == Game.winner_id,
        isouter=True,
    ).group_by(
        Game.id,
    ).order_by(
        Game.datetime,
    )
    res = await session.execute(stmt)
    converted_rows: list[dict] = []
    for row in res.all():
        row = dict(row._mapping)  # pylint: disable=protected-access
        if row['id'] is None:
            continue
        row['players'] = json.loads(row['players'])
        row['winner'] = json.loads(row['winner'])
        converted_rows.append(row)
    return converted_rows


async def fake_video_streamer():
    with open('static/test_video.mp4', mode='rb') as file:
        yield file.read()


@router.get('/{id}/video')
async def generate_video(id: int, session: AsyncSession = Depends(get_session)):  # pylint: disable=redefined-builtin
    stmt = select(Game.raw_data).where(Game.id == id)
    await session.execute(stmt)
    return StreamingResponse(fake_video_streamer(), media_type='video/mp4')


@router.post('')
async def write_game_data(data: HistorySchema, session: AsyncSession = Depends(get_session)):
    stmt = insert(
        Player,
    ).values([
        {'ip': player.ip, 'name': player.name}
        for player in data.players
    ]).on_conflict_do_update(set_={'name': Player.name}).returning(
        Player,
    )
    res = await session.execute(stmt)
    players = list(res.scalars())

    winner_id: int | None = None
    for player in players:
        if player.ip == data.winner.ip and player.name == data.winner.name:
            winner_id = player.id

    stmt = insert(
        Game,
    ).values(
        datetime=datetime.utcnow(),
        winner_id=winner_id,
        seed=data.map.seed,
        raw_data=data.json(),
    ).returning(Game)
    res = await session.execute(stmt)
    game = res.scalar_one()

    stmt = insert(
        PlayerGameLink,
    ).values([
        {'player_id': player.id, 'game_id': game.id}
        for player in players
    ])
    await session.execute(stmt)

    await session.commit()
    return {}
