"""
Gravity Simulator
description: It represents Newton's law of universal gravitation by
simulating some planets and using his equation on them.

version: 1 - beta
author: DisFunSec
"""
from tkinter import Canvas, Label, Tk

frame_rate = 1
gravity_constanta = 0.0001


def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x - r, y - r, x + r, y + r, **kwargs)


Canvas.create_circle = _create_circle


class Point:
    x: float
    y: float

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Gravity:
    grav_const = gravity_constanta

    def equation(self, dist=1.0, m1=1.0):
        if dist > 0:
            return (self.grav_const * m1) / dist ** 2
        elif dist == 0:
            return 0
        else:
            raise Exception(f"Impossible args: dist={dist}, m1={m1}.")


gravity = Gravity()


class Vector:
    cos: float
    sin: float
    len: float

    def init1(self, x: float, y: float):
        self.len = (x ** 2 + y ** 2) ** (1 / 2)
        if self.len != 0:
            self.cos = x / self.len
            self.sin = y / self.len
        else:
            self.sin = 1
            self.cos = 1

    def __init__(self, point: Point):
        self.init1(point.x, point.y)

    def get(self):
        return self.cos, self.sin, self.len


class Display:
    canvas: Canvas
    label: Label
    root: Tk
    bodies = []
    drawn_bodies = []
    cam = None
    drag_pos = Point(0, 0)

    def update_pos(self, event):
        tx = self.cam.x + (event.x - 500) / self.cam.zoom
        ty = self.cam.y + (event.y - 250) / self.cam.zoom
        self.root.title(f"GravSim v1 - beta    x: {tx} y: {ty}")

    def zoom_event(self, e):
        self.cam.zoom *= 1.2 ** (e.delta / 120)
        # self.update_pos()

    def move_start(self, event):
        self.drag_pos = Point(self.cam.x - event.x / self.cam.zoom, self.cam.y - event.y / self.cam.zoom)

    def move_cont(self, event):
        self.cam.x = event.x / self.cam.zoom + self.drag_pos.x
        self.cam.y = event.y / self.cam.zoom + self.drag_pos.y
        self.update_pos(event)

    def __init__(self):
        self.root = Tk()
        self.root.title("GravSim v1 - beta    x: 0 y: 0")
        self.canvas = Canvas(self.root, width=1000, height=500, bg="#000022")
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.move_start)
        self.canvas.bind('<B1-Motion>', self.move_cont)
        self.canvas.bind('<MouseWheel>', self.zoom_event)
        self.canvas.bind('<Motion>', self.update_pos)

    def lp1(self, cam):
        self.cam = cam
        for b in range(len(self.bodies)):
            body = self.bodies[b]
            r = 0
            self.bodies[b].tag = self.canvas.create_oval(body.tag, body.pos.x - r, body.pos.y - r, body.pos.x + r,
                                                         body.pos.y + r, fill=self.bodies[b].color)
        self.root.after(10, self.lp)
        self.root.mainloop()

    def lp(self):
        for b in range(len(self.bodies)):
            body = self.bodies[b]
            r = (body.mass ** 0.333) * 2 * self.cam.zoom
            tx = (body.pos.x + self.cam.x) * self.cam.zoom + 500
            ty = (body.pos.y + self.cam.y) * self.cam.zoom + 250
            self.canvas.coords(body.tag, tx - r, ty - r, tx + r, ty + r)
            self.bodies[b].move()
            for p1 in self.bodies:
                v = Vector(Point(body.pos.y - p1.pos.y, body.pos.x - p1.pos.x))
                f = gravity.equation(v.len, p1.mass)
                self.bodies[b].accelerate(Vector(Point(v.cos * f, v.sin * f)))
        self.root.after(frame_rate, self.lp)  # frame rate control


def add_v(v1: Vector, v2: Vector):
    return Vector(Point((v1.cos * v1.len + v2.cos * v2.len), (v1.sin * v1.len + v2.sin * v2.len)))


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
    x = 0
    y = 0
    zoom = 1

    def __init__(self):
        self.disp = Display()
        self.disp.bodies.append(Body(mass=400, pos=Point(-50, 0), color="red", vel=Vector(Point(0.01, 0))))
        self.disp.bodies.append(Body(mass=400, pos=Point(50, 0), color="yellow", vel=Vector(Point(-0.01, 0))))
        self.disp.bodies.append(Body(mass=0.1, pos=Point(0, 0), color="#00FF00", vel=Vector(Point(0, 0))))
        self.disp.lp1(self)


if __name__ == '__main__':
    Main()
