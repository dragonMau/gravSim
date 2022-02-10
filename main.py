"""
Gravity Simulator
description: It represents Newton's law of universal gravitation by
simulating some planets and using his equation on them.

version: 1.1 - beta
author: DisFunSec
"""
from tkinter import Canvas, Label, Tk
from sys import argv
from json import loads
from os.path import isdir, isfile
from os import listdir

#  load config from json
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

# configure max frame rate
frame_rate = config["other"]["frame rate"]


# make point data type
class Point:
    x: float
    y: float

    def __init__(self, x, y):
        self.x = x
        self.y = y


# make Gravity calculator
class Gravity:
    # configure grav_const
    grav_const = config["other"]["gravity const"]

    # method that takes distance and mass and returns gravity force
    def equation(self, dist=1.0, m1=1.0):
        if dist > 0:
            return (self.grav_const * m1) / dist ** 2
        elif dist == 0:
            return 0
        else:
            raise Exception(f"Impossible args: dist={dist}, m1={m1}.")


# init Gravity calculator
gravity = Gravity()


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
            self.sin = 1
            self.cos = 1

    def get(self):  # ok
        return self.cos, self.sin, self.len


#  this is shittiest piece of code
class Display:
    canvas: Canvas
    label: Label
    root: Tk
    bodies = []
    drawn_bodies = []
    cam = None
    drag_pos = Point(0, 0)

    def update_pos(self, event):  # update label with position of mouse on map
        tx = self.cam.x + (event.x - 500) / self.cam.zoom
        ty = self.cam.y + (event.y - 250) / self.cam.zoom
        self.root.title(f"GravSim v1.1  x: {tx} y: {ty}")

    def zoom_event(self, e):  # zooming(mouse wheel scrolling)
        self.cam.zoom *= 1.2 ** (e.delta / 120)

    def move_start(self, event):  # remember mouse drag start position on map
        self.drag_pos = Point(self.cam.x - event.x / self.cam.zoom, self.cam.y - event.y / self.cam.zoom)

    def move_cont(self, event):  # change cam position by dragging mouse
        self.cam.x = event.x / self.cam.zoom + self.drag_pos.x
        self.cam.y = event.y / self.cam.zoom + self.drag_pos.y
        self.update_pos(event)

    def __init__(self):  # tkinter sus
        self.root = Tk()
        self.root.title("GravSim v1.1  x: 0 y: 0")
        self.canvas = Canvas(self.root, width=1000, height=500, bg="#000022")
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.move_start)
        self.canvas.bind('<B1-Motion>', self.move_cont)
        self.canvas.bind('<MouseWheel>', self.zoom_event)
        self.canvas.bind('<Motion>', self.update_pos)

    # starting function
    def lp1(self, cam):
        self.cam = cam  # idk, copy cam to self class
        for b in range(len(self.bodies)):  # draw all bodies by ovals
            body = self.bodies[b]
            r = 0
            self.bodies[b].tag = self.canvas.create_oval(  # and give them their tag/uid
                body.tag,
                body.pos.x - r,
                body.pos.y - r,
                body.pos.x + r,
                body.pos.y + r,
                fill=self.bodies[b].color
            )
        self.root.after(10, self.lp)
        self.root.mainloop()

    # main loop function
    def lp(self):
        for b in range(len(self.bodies)):  # for each body
            body = self.bodies[b]
            r = (body.mass ** 0.333) * 2 * self.cam.zoom  # calculate bodies radius

            # graphics part
            tx = (body.pos.x + self.cam.x) * self.cam.zoom + 500  # calculate its position on screen
            ty = (body.pos.y + self.cam.y) * self.cam.zoom + 250
            self.canvas.coords(body.tag, tx - r, ty - r, tx + r, ty + r)  # update its position on screen

            # physics part
            self.bodies[b].move()  # move it
            vector = Vector(Point(0, 0))
            for p1 in self.bodies:  # sum every force that pulls/pushes the body
                direction = Vector(Point(body.pos.y - p1.pos.y, body.pos.x - p1.pos.x))  # direction
                direction.len = gravity.equation(direction.len, p1.mass)  # force
                vector = add_v(vector, direction)
            self.bodies[b].accelerate(vector)  # add to its velocity vector

        self.root.after(frame_rate, self.lp)  # loop main loop


# method to add vectors together, yea, maybe batter it will be on vector class, but...
def add_v(v1: Vector, v2: Vector):
    return Vector(Point((v1.cos * v1.len + v2.cos * v2.len), (v1.sin * v1.len + v2.sin * v2.len)))


# make body data type
class Body:
    mass: float
    pos: Point
    vel: Vector
    color: str
    tag = None

    def __init__(self, mass: int or float, pos: Point, vel: Vector = Vector(Point(0, 0)), color: str = "#FFFFFF"):
        self.mass = mass
        self.pos = pos
        self.vel = vel
        self.color = color

    def get(self):
        return self.mass, self.vel, self.pos

    def move(self):
        self.pos.y -= self.vel.cos * self.vel.len
        self.pos.x -= self.vel.sin * self.vel.len

    def accelerate(self, force_v: Vector):
        self.vel = add_v(self.vel, force_v)


class Main:
    x: float
    y: float
    zoom: float

    def __init__(self):  # load other configurations
        self.x = float(config["camera_position"]["x"])
        self.y = float(config["camera_position"]["y"])
        self.zoom = float(config["camera_position"]["zoom"])

        self.disp = Display()
        for planet in config["planets"]:  # append all planets
            self.disp.bodies.append(Body(
                mass=planet["mass"],
                pos=Point(planet["pos"]["x"], planet["pos"]["y"]),
                color=planet["color"],
                vel=Vector(Point(planet["vel"]["dx"], planet["vel"]["dy"])))
            )
        self.disp.lp1(self)  # start


if __name__ == '__main__':
    Main()
