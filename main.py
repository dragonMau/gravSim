"""
Gravity Simulator
description: It represents Newton's law of universal gravitation by
simulating some planets and using his equation on them.

version: 1.6 - beta
author: DisFunSec
"""
import time
from math import pi
from tkinter import Canvas, Label, Tk, StringVar
from sys import argv
from json import loads
from os.path import isdir, isfile
from os import listdir
from threading import Thread
from vector import Vector


# make point data type
class Point:
    x: float
    y: float

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_from(self, p):
        self.x = p.x
        self.y = -p.y

    def __mul__(self, num: int or float):
        return Point(self.x * num, self.y * num)


# make Gravity calculator
class Gravity:
    grav_const = 6.67 * 10 ** -11

    # method that takes distance and mass and returns gravity force
    @staticmethod
    def equation(dist=1.0, b1=None, b2=None):
        if b1.tag == b2.tag:
            return 0
        force = 0
        fg = 0
        if dist > 0:
            fg = (Gravity.grav_const * b2.mass * b1.mass) / dist ** 2
        force += fg

        v = Gravity.sphere_overlap(b1.r, b2.r, dist)
        c = ((b2.p * fg/b1.mass * v) + (b1.p * fg/b2.mass * v))/4
        force -= c

        a = force/b1.mass
        # print(b1.color, c, fg, force, a)
        return a

    @staticmethod
    def sphere_overlap(r1, r2, d):
        pm1 = r1 - ((r1 ** 2 - r2 ** 2) / (2 * d) + d / 2)
        pm2 = (r1 ** 2 - r2 ** 2) / (2 * d) + d / 2 - (d - r2)
        return Gravity.sphere_segment(r1, pm1) + Gravity.sphere_segment(r2, pm2)

    @staticmethod
    def sphere_segment(r, h=""):
        if h == "":
            h = 2 * r
        if h > 2 * r:
            h = 2 * r
        if h < 0:
            h = 0
        return pi * h ** 2 * (r - h / 3)


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
    info: StringVar

    def hook(self, event):
        tx = (event.x - self.canvas.winfo_width() / 2) / self.cam.zoom - self.cam.pos.x
        ty = self.cam.pos.y - (event.y - self.canvas.winfo_height() / 2) / self.cam.zoom
        for planet in self.bodies:
            dist = Vector(tx - planet.pos.x, ty - planet.pos.y).len
            if dist < planet.r:
                self.hooked_planet = planet.tag - 1
                return
        self.hooked_planet = None

    def toggle_pause(self):
        self.delta_t = self.frame_rate - self.delta_t
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
        self.info.set(f"x: {tx}\ny: {ty}")

    def zoom_event(self, e):  # zooming(mouse wheel scrolling)
        self.cam.zoom *= 10 ** (e.delta / 120 / 10)
        self.update_title()

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
        self.root.title("GravSim v1.6")

        self.canvas = Canvas(self.root, bg="#000022")
        self.canvas.pack(fill="both", expand=True)
        self.pause_label = Label(self.canvas, text="Paused", width=20, height=2)
        self.pause_label.place(x=15, y=15, anchor="nw")

        self.info = StringVar()
        self.info_label = Label(self.canvas, textvariable=self.info, width="20", height="2", bg="#0a0a44", anchor="w",
                                fg="white")
        self.info_label.place(relx=1.0, x=-15, y=15, anchor="ne")

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
            for body in self.bodies:
                body.r = ((body.mass / body.p) * 0.75 * pi) ** (1/3)
                vector = Vector(0, 0)
                for p1 in self.bodies:  # sum every force that pulls/pushes the body
                    direction = Vector(body.pos.x - p1.pos.x, body.pos.y - p1.pos.y)  # direction
                    direction.len = Gravity.equation(direction.len, body, p1)  # force
                    vector += direction
                body.accelerate(vector, self.delta_t)  # add to its velocity vector
            for b in self.bodies:
                b.move(self.delta_t)  # move it


# make body data type
class Body:
    mass: float
    pos: Point
    vel: Vector
    color: str
    tag = None
    r = 1
    p = 5520

    def __init__(self, mass: int or float, pos: Point, vel: Vector = Vector(0, 0), color: str = "#FFFFFF", p=1):
        self.mass = mass
        self.pos = pos
        self.vel = vel
        self.color = color
        self.p = p

    def get(self):
        return self.mass, self.vel, self.pos

    def move(self, dt):
        self.pos.y -= self.vel.y() * dt
        self.pos.x -= self.vel.x() * dt

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
            with open("./config.json", "r") as tf:
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
                vel=Vector(planet["vel"]["dx"], planet["vel"]["dy"]),
                p=(planet["p"])
            ))
        self.disp.lp1(self)  # start


if __name__ == '__main__':
    Main()
