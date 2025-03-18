"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from typing import Optional

import soundfile
import tcod
from tcod import libtcodpy

import core.color as color
import updates.constant
import game.entity_factories as entity_factories
import core.exceptions as exceptions
import core.input_handlers as input_handlers
import core.settings as settings
import updates.update_game
from components.scoreboard import get_score
from core.engine import Engine
from game.game_map import GameWorld

# Load the background image and remove the alpha channel.
background_image = tcod.image.load(
    "assets/images/menu_background.png")[:, :, :3]


class playerMenuMusic:
    """Class to handle the background music in the player menu."""

    def __init__(self, volume=None) -> None:
        self.player = None
        self.start(volume)

    def __call__(self, volume=None):
        if not volume:
            pass
        self.player.volume = volume

    def start(self, volume):
        """Start playing the background music."""
        mixer = tcod.sdl.audio.BasicMixer(
            tcod.sdl.audio.open()
        )  # Setup BasicMixer with the default audio output.
        sound, samplerate = soundfile.read(
            "assets/music/music.wav", dtype="float32"
        )  # Load an audio sample using SoundFile.
        song = mixer.device.convert(
            sound, samplerate
        )  # Convert this sample to the format expected by the device.
        self.player = mixer.play(
            song, volume=volume, loops=-1
            # Start asynchronous playback, audio is mixed on a separate Python thread.
        )

    def volume(self, volume):
        """Set the volume of the background music."""
        self.player.volume = self.volume


player_music = playerMenuMusic(settings.data_settings["volume"])


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80 + settings.data.screen_width
    map_height = 43 + settings.data.screen_height

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        screen_width=settings.data.screen_width,
        screen_height=settings.data.screen_height,
        player=player
    )

    engine.game_world.generate_floor()
    engine.update_fov()

    engine.message_log.add_message(
        "Good luck buddy, you will need it", color.welcome_text
    )

    return engine


def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(settings.data.path_folder + filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine


class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def __init__(self):
        self.selected = 0
        self.menu = [
            "  Continue last game",
            "  Play a new game",
            "  Scoreboard",
            "  Update",
            "  Settings",
            "  Quit",
        ]

        if not (settings.data.file_exists("savegame.sav")):
            self.menu.pop(0)

        self.lenght = len(self.menu)

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "~TOMBS OF THE LOST MIND~",
            fg=color.menu_title,
            bg=color.black,
            alignment=libtcodpy.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            "Made by: Pw-Wolf",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )
        menu_width = 24
        for i, text in enumerate(self.menu):
            if i != self.selected:
                console.print(
                    console.width // 2,
                    console.height // 2 - 2 + i,
                    text.ljust(menu_width),
                    fg=color.menu_text,
                    bg=color.black,
                    alignment=libtcodpy.CENTER,
                    bg_blend=libtcodpy.BKGND_ALPHA(64),
                )
            else:
                text = "->" + text[2:]
                console.print(
                    console.width // 2,
                    console.height // 2 - 2 + i,
                    text.ljust(menu_width),
                    fg=color.menu_text,
                    bg=color.selected,
                    alignment=libtcodpy.CENTER,
                    bg_blend=libtcodpy.BKGND_ALPHA(64),
                )

    def ev_keydown(
            self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        """Handle keydown events in the main menu."""

        name = settings.data_settings["name"]

        if name == "":
            return input_handlers.PopupMessageChangeKey(
                self,
                "Type name you want to use: ",
                selected="name",
                name=name,
                menu=True
            )

        if event.sym in (tcod.event.KeySym.q, tcod.event.KeySym.ESCAPE):
            raise SystemExit()

        elif event.sym in (tcod.event.KeySym.w, tcod.event.KeySym.UP):
            self.selected -= 1
            if self.selected == -1:
                self.selected = self.lenght - 1

        elif event.sym in (tcod.event.KeySym.s, tcod.event.KeySym.DOWN):
            self.selected += 1
            if self.selected == self.lenght:
                self.selected = 0

        elif event.sym == tcod.event.KeySym.RETURN or event.sym == tcod.event.KeySym.SPACE:
            if self.menu[self.selected] == "  Continue last game":
                try:
                    return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
                except FileNotFoundError:
                    return input_handlers.PopupMessage(self, "No saved game to load.")
                except Exception as exc:
                    traceback.print_exc()  # Print to stderr.
                    return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
            elif self.menu[self.selected] == "  Play a new game":
                return input_handlers.MainGameEventHandler(new_game())
            elif self.menu[self.selected] == "  Scoreboard":
                return input_handlers.PopupScoreboard(self, get_score(limit=20, name=name), name)
            elif self.menu[self.selected] == "  Update":
                return Update()
            elif self.menu[self.selected] == "  Settings":
                return Settings()
            elif self.menu[self.selected] == "  Quit":
                raise SystemExit()
            else:
                return None


class Update(input_handlers.BaseEventHandler):
    """Handle the Update logic and the rendering of the screen ."""

    def __init__(self) -> None:
        self.folder_folder = f"The_Lost_Mind_{updates.constant.VERSION}"

        self.game_exe = "The_Lost_Mind.exe"

        self.game_folder = "data"

        self.checking = True
        self.update = None
        self.updateGame = True
        self.updating = None
        self.done = None
        self.update_msg = "There is an update for this game it's version\nDo you want to update it"

    def on_render(self, console: tcod.Console) -> None:
        """Render the update screen."""
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8
        console.draw_semigraphics(background_image, 0, 0)
        text_print = []

        console.print(
            console.width // 2,
            console.height // 2 - 18,
            "TOMBS OF THE LOST MIND\n\nUpdate" + "\n" * 30 +
            f"Current game version:{updates.constant.VERSION}",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )

        if self.checking:
            text_print = ["Checking for updates"]

        elif self.updating:
            text_print = ["Updating the game"]

        elif self.done:
            text_print = ["Updating is done and the new version is installed\n\n\n\n",
                          "Press any key to restart the game"]

        elif not (self.update):
            text_print = ["Update is not availble"]
            self.done = True

        elif self.updateGame:
            text_print = [
                "Update avalible", "Do you want to update the game?", "", "", "", "->Yes ", "  No  "]
        elif not (self.updateGame):
            text_print = [
                "Update avalible", "Do you want to update the game?", "", "", "",  "  Yes ", "->No  "]

        for i, txt in enumerate(text_print):
            if "->" in txt or "restart" in txt:
                console.print(
                    console.width // 2,
                    console.height // 2 + i,
                    txt,
                    fg=color.menu_text,
                    bg=color.rose_red,
                    alignment=libtcodpy.CENTER,
                    bg_blend=libtcodpy.BKGND_ALPHA(64),
                )
                continue
            console.print(
                console.width // 2,
                console.height // 2 + i,
                txt,
                fg=color.menu_text,
                bg=color.black,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )

        if self.checking:
            self.update = updates.update_game.check_updates()
            self.checking = False

        if self.updating:
            self.updating_game()

    def updating_game(self):
        """Handle the game updating process."""
        self.update = updates.update_game.download_game()
        self.update = updates.update_game.manipultion_files()

        self.checking = None
        self.update = None
        self.updateGame = None
        self.updating = None
        self.done = True

    def ev_keydown(
            self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        """Handle keydown events in the update screen."""
        if event.sym in (tcod.event.KeySym.q, tcod.event.KeySym.ESCAPE):
            return MainMenu()

        if self.done:
            return MainMenu()

        if self.checking or not (self.update):
            return None

        elif event.sym in (tcod.event.KeySym.w, tcod.event.KeySym.s, tcod.event.KeySym.a, tcod.event.KeySym.d, tcod.event.KeySym.UP, tcod.event.KeySym.DOWN, tcod.event.KeySym.LEFT, tcod.event.KeySym.RIGHT):
            self.updateGame = not (self.updateGame)

        elif event.sym == tcod.event.KeySym.RETURN or event.sym == tcod.event.KeySym.SPACE:
            if self.updateGame:
                self.updating = True
                return None
            return MainMenu()


class Settings(input_handlers.BaseEventHandler):
    """Handle the settings rendering and input."""

    def __init__(self) -> None:
        self.data = self.get_settings()
        self.option_list = [
            item
            for sublist in (
                [i for i in self.data[key].keys()] if type(val) is dict else [key]
                for key, val in self.data.items()
            )
            for item in sublist
        ]
        self.selected = 0
        self.text_selected = self.option_list[self.selected]

    def get_settings(self):
        """Retrieve the current settings."""
        return settings.data_settings

    def default_setting(self):
        """Reset a setting to its default value."""
        settings.data_settings["controls"][self.text_selected] = settings.DEFAULT_SETTINGS["controls"][
            self.text_selected
        ]

    def on_render(self, console: tcod.Console) -> None:
        """Render the settings screen."""
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8
        console.draw_semigraphics(background_image, 0, 0)
        self.text_selected = self.option_list[self.selected]

        console.print(
            console.width // 2,
            console.height // 2 - 18,
            "TOMBS OF THE LOST MIND\n\nSettings",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )

        self.data = self.get_settings()
        menu_width = 48
        i = 0

        controls_lenght = 0
        for controls_lenght, text in enumerate(self.data["controls"]):
            bg_color = color.black
            select = "  "
            if self.text_selected == text:
                select = "<-"
                bg_color = color.selected

            text = (
                self.structure_setting(
                    text, menu_width, self.data["controls"][text])
                + select
            )
            console.print(
                console.width // 2,
                console.height // 2 - 10 + i,
                text.ljust(menu_width).ljust(menu_width),
                fg=color.menu_text,
                bg=bg_color,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )
            console.print(
                console.width // 2,
                console.height // 2 - 10 + i + 1,
                "".ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )
            i += 2

        text_to_print = []

        text = f"Username: {self.data['name']}  "
        if self.text_selected == "name":
            text = text[:-2] + "<-"
        text_to_print.append(text)

        text = f"Theme classic: {self.data['theme_classic']}  "
        if self.text_selected == "theme_classic":
            text = text[:-2] + "<-"
        text_to_print.append(text)

        text = f"Fullscreen: {self.data['fullscreen']}  "
        if self.text_selected == "fullscreen":
            text = f"Fullscreen: {self.data['fullscreen']}  "
            text = text[:-2] + "<-"
        text_to_print.append(text)

        text = f"Volume: {self.data['volume']}  "
        if self.text_selected == "volume":
            text = text[:-2] + "<-"
        text_to_print.append(text)

        for num, txt in enumerate(text_to_print):
            bg_color = color.black
            if "<-" in txt:
                bg_color = color.selected
            console.print(
                console.width // 2,
                console.height // 2 - 7 + i + num,
                txt,
                fg=color.menu_text,
                bg=bg_color,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )
        console.print(
            console.width // 2,
            console.height // 2 - 10 - 2,
            f"CONTROLS{'\n'*29}GENERAL",
            fg=color.menu_text,
            bg=color.black,
            alignment=libtcodpy.CENTER,
            bg_blend=libtcodpy.BKGND_ALPHA(64),
        )

    def structure_setting(self, text, menu_width, key):
        """Format the setting text for display."""
        spaces = menu_width - len(text) - len(key)
        if "_" in key:
            key = key.split("_")[1]
            spaces += len(key.split("_")[0]) + 2
        elif "N" in key and len(key) == 2:
            key = key.split("N")[1]
            spaces += len(key.split("N")[0])
        return text.replace("_", " ") + (" " * spaces) + key

    def ev_keydown(
            self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        """Handle keydown events in the settings screen."""
        if event.sym in (tcod.event.KeySym.q, tcod.event.KeySym.ESCAPE):
            raise exceptions.saveSettings()
        elif event.sym == tcod.event.KeySym.w or event.sym == tcod.event.KeySym.UP:
            if self.selected == 0:
                return None
            self.selected -= 1
        elif event.sym == tcod.event.KeySym.s or event.sym == tcod.event.KeySym.DOWN:
            if self.selected == (len(self.option_list) - 1):
                return None
            self.selected += 1

        elif event.sym == tcod.event.KeySym.a or event.sym == tcod.event.KeySym.LEFT:
            if self.text_selected == "theme_classic":
                settings.data_settings["theme_classic"] = not (
                    settings.data_settings["theme_classic"])
                return None
            elif self.text_selected == "volume":
                if settings.data_settings["volume"] == 0:
                    return None

                settings.data_settings["volume"] = round(
                    settings.data_settings["volume"] - 0.05, 2)
                player_music(settings.data_settings["volume"])

            elif self.text_selected == "fullscreen":
                settings.data_settings["fullscreen"] = not (
                    settings.data_settings["fullscreen"])
                return None

        elif event.sym == tcod.event.KeySym.d or event.sym == tcod.event.KeySym.RIGHT:
            if self.text_selected == "theme_classic":
                settings.data_settings["theme_classic"] = not (
                    settings.data_settings["theme_classic"])
                return None

            elif self.text_selected == "volume":
                if settings.data_settings["volume"] == 1:
                    return None

                settings.data_settings["volume"] = round(
                    settings.data_settings["volume"] + 0.05, 2)
                player_music(settings.data_settings["volume"])

            elif self.text_selected == "fullscreen":
                settings.data_settings["fullscreen"] = not (
                    settings.data_settings["fullscreen"])
                return None

        elif event.sym == tcod.event.KeySym.RETURN:
            if self.text_selected == "name":
                return input_handlers.PopupMessageChangeKey(
                    self,
                    "Type name you want to use: ",
                    selected=self.text_selected,
                    name=self.data["name"],
                )
            elif self.text_selected == "theme_classic" or self.text_selected == "volume":
                return None
            return input_handlers.PopupMessageChangeKey(
                self, "Press key you want to change it to", selected=self.text_selected
            )

        elif event.sym == tcod.event.KeySym.BACKSPACE:
            if self.text_selected == "theme_classic" or self.text_selected == "volume" or self.text_selected == "name":
                return None
            self.default_setting()
            return input_handlers.PopupMessage(self, "Reset to default")

        return None
