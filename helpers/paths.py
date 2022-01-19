from os.path import join, dirname

FP_CONTAINER = join(dirname(__file__), 'osu_fp.txt')

class OsuFolderPath:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init_from_file__(FP_CONTAINER)
        return cls._instance

    def __init_from_file__(self, fp):
        with open(fp, "r") as file:
            self.fp = file.read()

    def get(self):
        return self.fp

    def set(self, fp):
        with open(FP_CONTAINER, "w") as file:
            file.write(fp)
        self.fp = fp


osu_fp = OsuFolderPath()


def complete_path(path, root, folder="", ext=None) -> str:
    if ":" not in path:  # Relative import
        path = join(root, folder, path)
    if ext is not None and not path.endswith(ext):
        path += ext
    return path
