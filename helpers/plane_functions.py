from .plane_classes import Vector, CartesianLine

def segment_fraction(fraction: float, p1: Vector, p2: Vector) -> Vector:
    return (p2-p1)*fraction + p1

def bezier(fraction: float, p: Vector, *args: Vector) -> Vector:
    if not args: return p
    new_points = [ segment_fraction(fraction, p1, p2) for p1, p2 in zip((p, *args), args) ]
    return bezier(fraction, *new_points)

def angles_are_rotating_clockwise(a1: float, a2: float, a3: float) -> bool:
    return ((a1 > a2) + (a2 > a3) + (a3 > a1)) >= 2

def find_circle_center(p1: Vector, p2: Vector, p3: Vector) -> Vector:
    bisector1 = CartesianLine.as_perp_bis_of_two_points(p1, p2)
    bisector2 = CartesianLine.as_perp_bis_of_two_points(p2, p3)
    return bisector1.intersection_point(bisector2)
