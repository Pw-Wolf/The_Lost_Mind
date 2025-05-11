import lzma
import pickle
from getpass import getuser
from os import makedirs
from os.path import exists, isfile

class Settings:
     _instance = None 
    
    def __new__(cls, filename: str):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.filename = filename
            cls._instance.screen_width = 80
            cls._instance.screen_height = 50
            cls._instance.path_folder = f'C:\\Users\\{getuser()}\\AppData\\Local\\The_Lost_Mind\\'
            cls._instance.DEFAULT_SETTINGS = {
                "controls": {
                    "up": "w",
                    "down": "s",
                    "left": "a",
                    "right": "d",
                    "inventory": "TAB",
                    "pick_up": "f",
                    "inventory_drop": "g",
                    "look_around": "x",
                    "stats": "c",
                    "wait": "q",
                    "stairs": "e",
                    "history": "v",
                    "restart": "BACKSPACE"
                },
                "name": "",
                "theme_classic": False,
                "fullscreen": False,
                "volume": 0.05
            }
            cls._instance.make_folder()
            cls._instance._data_settings = cls._instance.load_settings()

        return cls._instance

    @property
    def data_settings(self):
        return self._data_settings

    @data_settings.setter
    def data_settings(self, value):
        print("new value")
        if isinstance(value, dict):
            self._data_settings = value
        else:
            raise ValueError("Value must be a dictionary")

    def save_settings(self):
        """Save this Settings instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self.data_settings))
        with open(self.path_folder + self.filename, "wb") as f:
            f.write(save_data)

    def load_settings(self):
        """Load a Settings instance from a file."""
        if not isfile(self.path_folder + self.filename):
            save_data = lzma.compress(pickle.dumps(self.DEFAULT_SETTINGS))
            with open(self.path_folder + self.filename, "wb") as f:
                f.write(save_data)
            return self.DEFAULT_SETTINGS

        with open(self.path_folder + self.filename, "rb") as f:
            settings = pickle.loads(lzma.decompress(f.read()))
        return settings

    def file_exists(self, filename: str) -> bool:
        return isfile(self.path_folder + filename)

    def make_folder(self):
        if not exists(self.path_folder):
            makedirs(self.path_folder)


data = Settings("settings")
data_settings = data.data_settings
