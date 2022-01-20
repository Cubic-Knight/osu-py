from .plane_classes import Vector

def segment_fraction(fraction: float, p1: Vector, p2: Vector) -> Vector:
    return (p2-p1)*fraction + p1

def bezier(fraction: float, p1: Vector, p2:Vector, *args: Vector) -> Vector:
    if not args: return segment_fraction(fraction, p1, p2)
    new_points = [segment_fraction(fraction, args[i], args[i+1]) for i in range(len(args)-1)]
    return bezier(fraction, *new_points)

# TODO: extend plane_functions
#  - for find_circle_center: https://www.youtube.com/watch?v=VZFeyS76euI
