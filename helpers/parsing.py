from typing import Any


def apply_first_correct_function(s: str, funcs: tuple, default: Any = ...):
    for f in funcs:
        try:
            return f(s)
        except Exception:
            continue
    if default is not Ellipsis:
        return default
    raise ValueError(f"All given functions made an exception with '{s}'")


def split_get(s: str, sep: str, obj_funcs: list, defaults: list = None,
              max_split: int = -1, no_strip: bool = False, min_len: int = 0, max_len: int = 100):
    """
    Like str.split(), but can map specific functions on the results
    :param s: The string to split
    :param sep: The separator
    :param obj_funcs: The list of functions
        The functions are mapped one to one to the elements of the split. For an identity function, use str
        If the functions are placed in a tuple, they are tries sequentially until one returns an object
        If the functions are placed in a list, the same mechanism applies, but like a star expression (max 1 list)
    :param defaults: The list of default values. They are used if all functions fail to return an object
        To represent the absence of a default value, use "..."
    :param max_split: The maximum number of splits to do. -1 (default) means no limit
    :param no_strip: If this is False, all elements of the string will be stripped after the split
    :param min_len: The result will have at least that many elements (only if min_len <= max_len)
        If there is not enough elements after splitting, the result will be padded with elements of default
    :param max_len: The result will have at most that many elements (if min_len > max_len, min_len is ignored)
    """
    # Split s (and strip if not no_strip)
    args = [i if no_strip else i.strip() for i in s.split(sep, max_split)]
    # Try to resolve "starred expression" pattern; if there is no list, just ignore this step
    try:
        star = [isinstance(f, list) for f in obj_funcs].index(True)  # Find list
        star_span = len(args) - len(obj_funcs) + 1  # Find how many functions should be added to match the length of args
        obj_funcs = obj_funcs[:star] + [tuple(obj_funcs[star])]*star_span + obj_funcs[star+1:]
    except ValueError:
        pass
    # Convert every non-tuple function to a 1-tuple containing that function
    obj_funcs = [(f,) if not isinstance(f, tuple) else f for f in obj_funcs]
    # Extend obj_funcs and default so they match the length of args (too much is not a problem but too few is)
    if defaults is None: defaults = []
    obj_funcs.extend( (str,) for i in range(len(args)-len(obj_funcs)) )
    defaults.extend( ... for i in range(len(args)-len(defaults)) )
    res = [apply_first_correct_function(arg, funcs, default) for arg, funcs, default in zip(args, obj_funcs, defaults)]
    return ( res + defaults[len(res):min_len] )[:max_len]
