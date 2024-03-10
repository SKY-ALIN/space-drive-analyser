from typing import Sequence
import uuid
import random

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
import matplotlib.animation as animation
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


class Player(Object):
    color = 'red'
    font_color = 'white'
    font_size = 800

    def __init__(self, x: float, y: float, r: float, name: str):
        self.x = x
        self.y = y
        self.r = r
        self.name = name
        self.artist = plt.Circle((x, y), r, color=self.color)
        self.text: plt.Text | None = None

    def bind(self, space: 'Space'):
        space.ax.add_artist(self.artist)
        self.text = space.ax.text(
            self.x + self.r + 5,
            self.y,
            self.name,
            fontsize=self.font_size,
            color=self.font_color,
            ha='left',
            va='center',
        )

    def get_artists(self) -> Sequence[Artist]:
        return (self.artist, self.text) if self.text is not None else (self.artist,)

    def move(self, x: float, y: float):
        self.artist.center = (x, y)
        if self.text is not None:
            self.text.set_position((x + self.r + 5, y))

    def remove(self):
        self.artist.remove()
        if self.text is not None:
            self.text.remove()


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
    star_radius = 0.5

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
                self.star_radius,
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
        self.active_objects: set[Object] = set()

    def update_frame(self, frame: int) -> Sequence[Artist]:
        artists = []
        new_active_objects: set[Object] = set()
        for obj, (x, y) in self.mover.history[frame].items():
            if obj not in self.active_objects:
                self.space.add_object(obj)
            new_active_objects.add(obj)

            obj.move(x, y)
            artists.extend(obj.get_artists())

        for obj in self.active_objects.difference(new_active_objects):
            try:
                obj.remove()
            except ValueError as e:
                print(f"Error removing object: {e}")

        self.active_objects = new_active_objects

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
            for obj in state.objects:
                if obj.object == 'player':
                    obj: PlayerObjectSchema
                    if obj.id not in players:
                        player_data = players_data[obj.id]
                        player = Player(x=obj.x, y=obj.y, r=obj.r, name=player_data.name)
                        players[obj.id] = player
                    self.mover.move(players[obj.id], (obj.x, obj.y))
                elif obj.object == 'missile':
                    obj: MissileObjectSchema
                    if obj.id not in missiles:
                        missile = Missile(x=obj.x, y=obj.y)
                        missiles[obj.id] = missile
                    self.mover.move(missiles[obj.id], (obj.x, obj.y))
            self.mover.next()

    def make(self):
        self._add_passive_objects()
        self._add_active_objects()
        self.animator.animate()


if __name__ == "__main__":
    AnimatorController(HistorySchema.parse_file('res.json')).make()
