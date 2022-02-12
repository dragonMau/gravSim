"""
Gravity Simulator
description: It represents Newton's law of universal gravitation by
simulating some planets and using his equation on them.

version: 1.5 - beta
author: DisFunSec
"""
import time
from tkinter import Canvas, Label, Tk
from sys import argv
from json import loads
from os.path import isdir, isfile
from os import listdir
from threading import Thread


# make point data type
class Point:
    x: float
    y: float

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_from(self, p):
        self.x = p.x
        self.y = p.y

    def __mul__(self, num: int or float):
        return Point(self.x * num, self.y * num)


# make Gravity calculator
class Gravity:
    grav_const = 6.67 * 10 ** -11

    # method that takes distance and mass and returns gravity force
    @staticmethod
    def equation(dist=1.0, m1=1.0):
        if dist > 0:
            return (Gravity.grav_const * m1) / dist ** 2
        elif dist == 0:
            return 0
        else:
            raise Exception(f"Impossible args: dist={dist}, m1={m1}.")


# make vector data type
class Vector:
    cos: float
    sin: float
    len: float

    # creating vector
    def __init__(self, point: Point):
        x, y = point.x, point.y
        self.len = (x ** 2 + y ** 2) ** (1 / 2)  # Pythagoras
        try:  # a piece from trigonometry to configure direction
            self.cos = x / self.len
            self.sin = y / self.len
        except ZeroDivisionError:  # even math isn't perfect
            self.sin = 0
            self.cos = 1

    def get(self, *whats):  # ok
        if whats == ():
            return self.cos, self.sin, self.len
        else:
            return_ = ()
            for what in whats:
                if what in ["sin", "cos", "len"]:
                    return_ += (self.__getattribute__(what),)
                elif what == "x":
                    return_ += (self.cos * self.len,)
                elif what == "y":
                    return_ += (self.sin * self.len,)
            if len(return_) == 1:
                return return_[0]
            return return_

    def __add__(self, v2):
        return Vector(Point((self.get("x") + v2.get("x")), (self.get("y") + v2.get("y"))))

    def __mul__(self, other):
        if type(other) in (int, float):
            return Vector(Point(self.len * self.cos * other, self.len * self.sin * other))


class Display:
    canvas: Canvas
    label: Label
    root: Tk
    bodies = []
    drawn_bodies = []
    cam = None
    drag_pos = Point(0, 0)
    enabled = True
    hooked_planet = None
    loop1: Thread
    mouse_pos = Point(0, 0)
    delta_t = 0
    fullscreen = 0

    def hook(self, event):
        tx = (event.x - self.canvas.winfo_width() / 2) / self.cam.zoom - self.cam.pos.x
        ty = self.cam.pos.y - (event.y - self.canvas.winfo_height() / 2) / self.cam.zoom
        for planet in self.bodies:
            dist = Vector(Point(tx - planet.pos.x, ty - planet.pos.y)).len
            if dist < planet.r:
                self.hooked_planet = planet.tag - 1
                return
        self.hooked_planet = None

    def toggle_pause(self):
        self.delta_t = 1 - self.delta_t
        if not self.delta_t:
            self.pause_label.place(x="15", y="15", anchor="nw")
        else:
            self.pause_label.place_forget()

    def toggle_fullscreen(self):
        self.fullscreen = 1 - self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def keyboard_interrupt(self, e):
        if e.keysym == "Escape":
            self.toggle_pause()
        elif e.keysym == "F11":
            self.toggle_fullscreen()
        # else: print(e)

    def stop(self):
        self.enabled = False
        self.root.destroy()

    def update_mouse_pos(self, event):
        self.mouse_pos = Point(event.x, event.y)
        self.update_title()

    def update_title(self):  # update label with position of mouse on map
        tx = (self.mouse_pos.x - self.canvas.winfo_width() / 2) / self.cam.zoom - self.cam.pos.x
        ty = self.cam.pos.y - (self.mouse_pos.y - self.canvas.winfo_height() / 2) / self.cam.zoom
        self.root.title(f"GravSim v1.5  x: {round(tx, 2)} y: {round(ty, 2)}," +
                        f" cam(x: {round(self.cam.pos.x, 2)} y: {round(self.cam.pos.y, 2)})")

    def zoom_event(self, e):  # zooming(mouse wheel scrolling)
        self.cam.zoom *= 1.2 ** (e.delta / 120)

    def move_start(self, event):  # remember mouse drag start position on map
        self.drag_pos = Point(self.cam.pos.x - event.x / self.cam.zoom,
                              self.cam.pos.y - event.y / self.cam.zoom)

    def move_cont(self, event):  # change cam position by dragging mouse
        if self.hooked_planet is None:
            self.cam.pos.x = self.drag_pos.x + event.x / self.cam.zoom
            self.cam.pos.y = self.drag_pos.y + event.y / self.cam.zoom
            self.update_mouse_pos(event)

    def __init__(self, frame_rate):  # tkinter sus
        self.root = Tk()
        self.root.title("GravSim v1.5  x: 0 y: 0")

        self.canvas = Canvas(self.root, bg="#000022")
        self.canvas.pack(fill="both", expand=True)
        self.pause_label = Label(self.canvas, text="Paused", width="20", height="2", anchor="center")
        self.pause_label.place(x="15", y="15", anchor="nw")

        self.canvas.bind('<Button-1>', self.move_start)
        self.canvas.bind('<B1-Motion>', self.move_cont)
        self.canvas.bind('<MouseWheel>', self.zoom_event)
        self.canvas.bind('<Motion>', self.update_mouse_pos)
        self.canvas.bind('<Double-Button-1>', self.hook)
        self.root.bind('<Key>', self.keyboard_interrupt)
        self.frame_rate = frame_rate
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.stop())

        self.root.geometry("1000x500")
        self.root.update()

    # starting function
    def lp1(self, cam):
        self.cam = cam
        for b in range(len(self.bodies)):
            body = self.bodies[b]
            r = 0
            self.bodies[b].tag = self.canvas.create_oval(
                body.tag,
                body.pos.x - r,
                body.pos.y - r,
                body.pos.x + r,
                body.pos.y + r,
                fill=self.bodies[b].color
            )
        self.update_phys()

    def update_graph(self):
        if self.hooked_planet is not None:
            self.cam.pos.get_from(self.bodies[self.hooked_planet].pos * -1)
            self.update_title()
        for b in range(len(self.bodies)):  # for each body
            body = self.bodies[b]
            r = body.r * self.cam.zoom
            tx = (body.pos.x + self.cam.pos.x) * self.cam.zoom + self.canvas.winfo_width() / 2
            ty = (- body.pos.y + self.cam.pos.y) * self.cam.zoom + self.canvas.winfo_height() / 2
            self.canvas.coords(body.tag, tx - r, ty - r, tx + r, ty + r)
        self.root.update()

    def update_phys(self):  # mainloop
        t_0 = time.time()
        while self.enabled:
            while time.time() - t_0 < self.frame_rate:
                self.update_graph()
            t_0 = time.time()
            for b in range(len(self.bodies)):
                body = self.bodies[b]
                self.bodies[b].r = (body.mass ** 0.333) * 2
                self.bodies[b].move(self.delta_t)  # move it
                vector = Vector(Point(0, 0))
                for p1 in self.bodies:  # sum every force that pulls/pushes the body
                    direction = Vector(Point(body.pos.x - p1.pos.x, body.pos.y - p1.pos.y))  # direction
                    if direction.len > (body.r + p1.r):
                        direction.len = Gravity.equation(direction.len, p1.mass)  # force
                        vector += direction
                self.bodies[b].accelerate(vector, self.delta_t)  # add to its velocity vector


# make body data type
class Body:
    mass: float
    pos: Point
    vel: Vector
    color: str
    tag = None
    r = 1

    def __init__(self, mass: int or float, pos: Point, vel: Vector = Vector(Point(0, 0)), color: str = "#FFFFFF"):
        self.mass = mass
        self.pos = pos
        self.vel = vel
        self.color = color

    def get(self):
        return self.mass, self.vel, self.pos

    def move(self, dt):
        self.pos.y -= self.vel.get("y") * dt
        self.pos.x -= self.vel.get("x") * dt

    def accelerate(self, force_v: Vector, dt):
        self.vel = self.vel + force_v * dt


class Main:
    pos = Point(0, 0)
    zoom: float

    @staticmethod
    def load_config():
        if len(argv) > 1:
            if isfile(argv[1]):
                with open(argv[1], "r") as tf:
                    config = loads(tf.read())  # any file by given path
            elif isdir(argv[1]):
                files = [file for file in listdir(argv[1]) if isfile(file)]
                if "config.json" in files:
                    with open(argv[1], "r") as tf:
                        config = loads(tf.read())  # 'config.json' on given directory
                else:
                    raise Exception(f"not found \"config.json\" in \"{argv[1]}\"")
            else:
                raise Exception(f"invalid path \"{argv[1]}\"")
        elif isfile("./config.json"):
            with open(argv[1], "r") as tf:
                config = loads(tf.read())  # default configuration
        else:
            raise Exception("not found \"config.json\"")
        return config

    def __init__(self):  # load other configurations
        self.config = self.load_config()

        self.pos.x = float(self.config["camera_position"]["x"])
        self.pos.y = float(self.config["camera_position"]["y"])
        self.zoom = float(self.config["camera_position"]["zoom"])

        Gravity.grav_const = self.config["other"]["gravity const"]

        self.disp = Display(1 / self.config["other"]["frame rate"])
        for planet in self.config["planets"]:  # append all planets
            self.disp.bodies.append(Body(
                mass=planet["mass"],
                pos=Point(planet["pos"]["x"], planet["pos"]["y"]),
                color=planet["color"],
                vel=Vector(Point(planet["vel"]["dx"], planet["vel"]["dy"])))
            )
        self.disp.lp1(self)  # start


if __name__ == '__main__':
    Main()
