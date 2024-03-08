from typing import Sequence
import uuid
import random
import json

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from schemas import HistorySchema, PlayerObjectSchema, MissileObjectSchema


class Object:
    def bind(self, space: 'Space'):
        raise NotImplementedError

    def get_artists(self) -> Sequence[Artist]:
        raise NotImplementedError

    def move(self, x: float, y: float):
        pass

    def remove(self):
        pass

    def __hash__(self):
        return hash(uuid.uuid4())


class Player(Object):
    def __init__(self, x: float, y: float, r: float, name: str):
        self.name = name
        self.artist = plt.Circle((x, y), r, color='r')
        self.text = plt.Text(x+50, y+50, name, fontsize=24, ha='center', va='center', color='g')

    def bind(self, space: 'Space'):
        space.ax.add_artist(self.artist)
        space.ax.add_artist(self.text)

    def get_artists(self) -> Sequence[Artist]:
        return self.artist, self.text

    def move(self, x: float, y: float):
        self.artist.center = (x, y)
        self.text.center = (x+50, y+50)

    def remove(self):
        self.artist.remove()
        self.text.remove()


class Missile(Object):
    def __init__(self, x: float, y: float):
        self.artist = plt.Circle((x, y), 3, color='y')

    def bind(self, space: 'Space'):
        space.ax.add_artist(self.artist)

    def get_artists(self) -> Sequence[Artist]:
        return self.artist,

    def move(self, x: float, y: float):
        self.artist.center = (x, y)

    def remove(self):
        self.artist.remove()


class Barrier(Object):
    def __init__(self, x: float, y: float, r: float):
        self.artist = plt.Circle((x, y), r, color='grey')

    def bind(self, space: 'Space'):
        space.ax.add_artist(self.artist)

    def get_artists(self) -> Sequence[Artist]:
        return self.artist,


class Mover:
    def __init__(self):
        self.history: list[dict[Object, tuple[float, float]]] = [{}]

    def move(self, o: Object, data: tuple[float, float]):
        self.history[-1][o] = data

    def next(self):
        self.history.append({})


class Space:
    color = '#000000'
    stars_color = '#FFFFFF'
    stars_amount = 200
    dpi = 4

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        self.fig = plt.figure(figsize=(width, height), dpi=self.dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_facecolor(self.color)
        self._generate_stars()

    def _generate_stars(self):
        for _ in range(self.stars_amount):
            self.ax.add_artist(plt.Circle(
                (
                    random.randint(0, int(self.width)),
                    random.randint(0, int(self.height))
                ),
                1,
                color=self.stars_color,
            ))

    def add_object(self, obj: Object):
        obj.bind(self)

    def show(self):
        FigureCanvas(self.fig).print_figure('test.png')


class Animator:
    frame_interval = 50

    def __init__(self, space: Space, mover: Mover):
        self.space = space
        self.mover = mover

    def update_frame(self, frame: int) -> Sequence[Artist]:
        artists = []
        for obj, (x, y) in self.mover.history[frame].items():
            obj.move(x, y)
            artists.extend(obj.get_artists())
        return artists

    def animate(self):
        a = animation.FuncAnimation(
            fig=self.space.fig,
            func=self.update_frame,
            frames=len(self.mover.history),
            interval=self.frame_interval,
        )
        a.save('test.mp4')


class AnimatorController:
    def __init__(self, history: HistorySchema):
        self.history = history
        self.mover = Mover()
        self.space = Space(width=self.history.map.width, height=self.history.map.height)
        self.animator = Animator(space=self.space, mover=self.mover)

    def _add_passive_objects(self):
        for barrier in self.history.map.barriers:
            self.space.add_object(Barrier(x=barrier.x, y=barrier.y, r=barrier.r))

    def _add_active_objects(self):
        players_data = {player.id: player for player in self.history.players}
        players: dict[int, Player] = {}
        missiles: dict[int, Missile] = {}
        for state in self.history.history:
            active_objects: set[Object] = set()
            for obj in state.objects:
                if obj.object == 'player':
                    obj: PlayerObjectSchema
                    if obj.id not in players:
                        player_data = players_data[obj.id]
                        player = Player(x=obj.x, y=obj.y, r=obj.r, name=player_data.name)
                        players[obj.id] = player
                        self.space.add_object(player)
                    self.mover.move(players[obj.id], (obj.x, obj.y))
                    active_objects.add(players[obj.id])
                elif obj.object == 'missile':
                    obj: MissileObjectSchema
                    if obj.id not in missiles:
                        missile = Missile(x=obj.x, y=obj.y)
                        missiles[obj.id] = missile
                        self.space.add_object(missile)
                    self.mover.move(missiles[obj.id], (obj.x, obj.y))
                    active_objects.add(missiles[obj.id])

            player_ids_to_delete = []
            for player_id, obj in players.items():
                if obj not in active_objects:
                    obj: Player
                    obj.remove()
                    player_ids_to_delete.append(player_id)
            for player_id in player_ids_to_delete:
                del players[player_id]

            missile_ids_to_delete = []
            for missile_id, obj in missiles.items():
                if obj not in active_objects:
                    obj: Missile
                    obj.remove()
                    missile_ids_to_delete.append(missile_id)
            for missile_id in missile_ids_to_delete:
                del missiles[missile_id]

            self.mover.next()

    def make(self):
        self._add_passive_objects()
        self._add_active_objects()
        self.animator.animate()


if __name__ == "__main__":
    AnimatorController(HistorySchema.parse_file('res.json')).make()
