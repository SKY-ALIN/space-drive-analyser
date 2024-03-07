from typing import Sequence
import uuid
import random

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


class Object:
    def bind(self, space: 'Space'):
        pass

    def get_artists(self) -> Sequence[Artist]:
        pass

    def move(self, x: float, y: float):
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
    stars_amount = 300
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
    def __init__(self, space: Space, mover: Mover):
        self.space = space
        self.mover = mover

    def update_frame(self, frame: int):
        if frame == 0:
            return ()
        artists = []
        for obj, (x, y) in self.mover.history[frame-1].items():
            obj.move(x, y)
            artists.extend(obj.get_artists())
        return artists

    def animate(self):
        a = animation.FuncAnimation(
            fig=self.space.fig,
            func=self.update_frame,
            frames=len(self.mover.history) + 1,
        )
        a.save('test.mp4')


if __name__ == "__main__":
    s = Space(1500.0, 1000.0)
    p = Player(100, 100, 50, "Skyler")
    s.add_object(p)
    s.add_object(Barrier(1000, 1000, 100))

    m = Mover()
    m.move(p, (110, 110))
    m.next()
    m.move(p, (120, 120))
    m.next()
    m.move(p, (130, 130))
    m.next()
    m.move(p, (130, 140))
    m.next()
    m.move(p, (130, 150))
    m.next()
    m.move(p, (130, 160))

    Animator(s, m).animate()
