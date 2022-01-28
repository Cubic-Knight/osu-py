def zigzag_function(rise_x, rise_y=None, fall_x=None, fall_y=None, start_x=0, start_y=0):
    if rise_y is None: rise_y = rise_x
    if fall_x is None: fall_x = rise_x
    if fall_y is None: fall_y = -rise_y

    def inner(x: float) -> float:
        spikes_passed = (x - start_x + fall_x) // (rise_x + fall_x)
        rel_x = (x - start_x + fall_x) % (rise_x + fall_x) - fall_x
        base = spikes_passed * (rise_y + fall_y)
        spike = rise_y * (rel_x/rise_x) if rel_x > 0 else fall_y * (rel_x/fall_x)
        return base + spike + start_y
    return inner

"""
# If you want to try it out for yourself:

func = zigzag_function(10, 3, 5, -5)

import matplotlib.pyplot as plt
plt.plot([func(i) for i in range(100)])
plt.show()
"""
