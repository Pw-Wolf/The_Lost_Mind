from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Callable, Optional, Tuple, Union

import tcod

import core.actions as actions
import core.color as color
import components.scoreboard
import core.exceptions as exceptions
import core.settings as settings
from core.actions import Action, BumpAction, PickupAction, WaitAction
from core.engine import Engine

if TYPE_CHECKING:
    from core.engine import Engine
    from game.entity import Item

from tcod import libtcodpy


def player_controls():
    global MOVE_KEYS, INTERACTION_KEYS, WAIT_KEYS, CONFIRM_KEYS, CURSOR_Y_KEYS
    MOVE_KEYS = {
        # Arrow keys
        tcod.event.KeySym.UP: (0, -1),
        tcod.event.KeySym.DOWN: (0, 1),
        tcod.event.KeySym.LEFT: (-1, 0),
        tcod.event.KeySym.RIGHT: (1, 0),

        # Custom
        getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["up"]}'): (0, -1),
        getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["down"]}'): (0, 1),
        getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["left"]}'): (-1, 0),
        getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["right"]}'): (1, 0)
    }

    INTERACTION_KEYS = {
        "inventory": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["inventory"]}'),
        "inventory_drop": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["inventory_drop"]}'),
        "pick_up": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["pick_up"]}'),
        "looKeySym.around": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["look_around"]}'),
        "stats": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["stats"]}'),
        "wait": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["wait"]}'),
        "stairs": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["stairs"]}'),
        "restart": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["restart"]}'),
        "history": getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["history"]}'),
    }

    WAIT_KEYS = {
        tcod.event.KeySym.PERIOD,
        tcod.event.KeySym.KP_5,
        tcod.event.KeySym.CLEAR,
        getattr(tcod.event.KeySym, f'{settings.data_settings["controls"]["wait"]}')
    }

    CONFIRM_KEYS = {
        tcod.event.KeySym.RETURN,
        tcod.event.KeySym.KP_ENTER,
        tcod.event.KeySym.SPACE,
    }

    CURSOR_Y_KEYS = {
        tcod.event.KeySym.UP: -1,
        tcod.event.KeySym.DOWN: 1,
        tcod.event.KeySym.PAGEUP: -10,
        tcod.event.KeySym.PAGEDOWN: 10,
    }


ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.
If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""
player_controls()


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8
        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=libtcodpy.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class PopupScoreboard(BaseEventHandler):
    """Display a popup text window with scoreboard."""

    def __init__(self, parent_handler: BaseEventHandler, scores: list, name: str):
        self.parent = parent_handler
        self.scores = scores.split("\n")
        self.name = name

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8
        for i, s in enumerate(self.scores):
            fg_color = color.white
            if self.name in s or "Best personal" in s:
                fg_color = color.rose_red

            console.print(
                console.width // 2,
                console.height // 4 + i,
                s,
                fg=fg_color,
                bg=color.black,
                alignment=libtcodpy.CENTER,
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class PopupMessageChangeKey(BaseEventHandler):
    """Display a popup text window when you change the settings."""

    def __init__(self, parent_handler: BaseEventHandler, text: str, selected: int, name="", menu=False):
        self.parent = parent_handler
        self.text = text
        self.selected = selected
        self.name = name
        self.menu = menu

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8
        console.print(
            console.width // 2,
            console.height // 2,
            self.text + self.name,
            fg=color.white,
            bg=color.black,
            alignment=libtcodpy.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        str_event = str(event)

        start = str_event.find("Scancode.") + len("Scancode.")
        end = str_event.find(",", start)
        key = str_event[start:end]

        start = str_event.find("mod=") + len("mod=")
        end = str_event.find(")", start)
        mod = str_event[start:end].split("|")
        case_sens = not (any("KMOD_CAPS" in s or "SHIFT" in s for s in mod))

        if "_" in key:
            key = key.split("_")[1]
        elif "N" in key and len(key) == 2:
            key = key.replace("N", "")
        if self.selected == "name":
            if key == "BACKSPACE":
                self.name = self.name[:-1]
                return
            elif key == "ESCAPE":
                if self.menu:
                    raise exceptions.QuitWithoutSaving
                return self.parent
            elif key == "RETURN":
                settings.data_settings[self.selected] = re.sub(r'[^a-zA-Z-_]', '', self.name)
                return self.parent
            elif key == "MINUS":
                if not (case_sens):
                    self.name += "_"
                    return
                self.name += "-"
                return
            elif len(key) > 3:
                return
            if case_sens:
                self.name += key.lower()
                return
            self.name += key
            return

        elif not (event.type == "TEXTINPUT"):
            if key == "ESCAPE" or key == "RETURN":
                return self.parent

            if len(key) < 3:
                key = key.lower()
            settings.data_settings["controls"][self.selected] = key
            return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.scoreboard_on = True

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.
        Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
                tcod.event.KeySym.LSHIFT,
                tcod.event.KeySym.RSHIFT,
                tcod.event.KeySym.LCTRL,
                tcod.event.KeySym.RCTRL,
                tcod.event.KeySym.LALT,
                tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.
        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        score = int((self.engine.player.level.current_level / 2) * (150 * (self.engine.player.level.current_level - 1)) + self.engine.player.level.current_xp)

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}\nXP: {self.engine.player.level.current_xp}\nXP for next Level: {self.engine.player.level.experience_to_next_level}\nScore: {score}\nAttack: {self.engine.player.fighter.power}\nDefense: {self.engine.player.fighter.defense}",
        )


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"
    SELECTED = 0
    LENGHT = 3

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!\nSelect an attribute to increase.")

        attributes = [f"Constitution (+20 HP, from {self.engine.player.fighter.max_hp})",
                      f"Strength (+1 attack, from {self.engine.player.fighter.power})",
                      f"Agility (+1 defense, from {self.engine.player.fighter.defense})"
                      ]
        for num, i in enumerate(attributes):
            if num == self.SELECTED:
                i = "->" + i
                fg_color = color.rose_red
            else:
                i = "  " + i
                fg_color = color.black

            console.print(
                x=x + 1,
                y=4 + num,
                string=i,
                bg=fg_color
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym

        if key in MOVE_KEYS:
            _, dy = MOVE_KEYS[key]
            self.SELECTED += dy

            if self.SELECTED == self.LENGHT:
                self.SELECTED = 0
            elif self.SELECTED == -1:
                self.SELECTED = self.LENGHT - 1

            return None

        elif key == tcod.event.KeySym.ESCAPE:
            raise exceptions.mainMenu()

        elif event.sym in CONFIRM_KEYS:
            match self.SELECTED:
                case 0:
                    player.level.increase_max_hp()
                case 1:
                    player.level.increase_power()
                case 2:
                    player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None


class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.
    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"
    SELECTED = 0
    LENGHT = 0

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        self.LENGHT = number_of_items_in_inventory

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory < 1:
            console.print(x + 1, y + 1, "(Empty)")
            return None

        for i, item in enumerate(self.engine.player.inventory.items):

            order = f"  "
            if i == self.SELECTED:
                order = f"->"

            is_equipped = self.engine.player.equipment.item_is_equipped(item)

            name = item.name

            if is_equipped:
                name = f"{item.name} (E)"

            console.print(x + 1, y + i + 1, order, fg=(255, 255, 255))
            console.print(x + 1 + 2, y + i + 1, name, fg=item.color)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym

        if key in MOVE_KEYS:
            _, dy = MOVE_KEYS[key]
            self.SELECTED += dy

            if self.SELECTED == self.LENGHT:
                self.SELECTED = 0
            elif self.SELECTED == -1:
                self.SELECTED = self.LENGHT - 1

            return None

        elif key == tcod.event.KeySym.ESCAPE:
            raise exceptions.mainMenu()

        elif event.sym == INTERACTION_KEYS["inventory"]:
            return super().ev_keydown(event)

        try:
            selected_item = player.inventory.items[self.SELECTED]
        except IndexError:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

        if key == INTERACTION_KEYS["inventory_drop"]:
            return actions.DropItem(self.engine.player, selected_item)

        elif event.sym in CONFIRM_KEYS or event.sym == INTERACTION_KEYS["pick_up"]:
            return self.on_item_selected(selected_item)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        self.player = self.engine.player
        self.centar = settings.data.screen_width//2, settings.data.screen_height//2
        self.first_pixel = self.player.x - self.centar[0], self.player.y - self.centar[1]
        engine.mouse_location = self.player.y, self.player.x

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        if y < settings.data.screen_height - 1 and x < settings.data.screen_width - 1:
            console.rgb["bg"][x, y] = color.white
            console.rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
            self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == INTERACTION_KEYS["stairs"]:
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.KeySym.ESCAPE:
            raise exceptions.mainMenu()
        elif key == INTERACTION_KEYS["history"]:
            return HistoryViewer(self.engine)

        elif key == INTERACTION_KEYS["pick_up"]:
            action = PickupAction(player)

        elif key == INTERACTION_KEYS["inventory"]:
            return InventoryActivateHandler(self.engine)

        elif key == INTERACTION_KEYS["looKeySym.around"]:
            return LookHandler(self.engine)

        elif key == INTERACTION_KEYS["restart"]:
            raise exceptions.Restart()

        elif key == INTERACTION_KEYS["stats"]:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.KeySym.m:
            pass
        # No valid key was pressed
        return action


class GameOverEventHandler(EventHandler):
    """It executes when the player dies and gets a scoreboard from a server"""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.TITLE = "Scoreboard"
        self.name = settings.data_settings["name"]
        score = int((self.engine.player.level.current_level / 2) * (150 * (self.engine.player.level.current_level - 1)) + self.engine.player.level.current_xp)
        self.get_score = components.scoreboard.get_score(limit=15, name=self.name)
        if self.get_score == "Timed out":
            self.get_score = ""
        self.score = self.get_score + f"Current score : {score}"
        self.score = self.score.split("\n")

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def restart(self) -> None:
        raise exceptions.Restart()

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 43
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 15
        height = 3
        if self.get_score:
            height = 21
            width = len(self.TITLE) + 27

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        for i, txt in enumerate(self.score[1:]):
            color_font = color.white
            if self.name in txt or "Current" in txt:
                color_font = color.rose_red
            elif "Best personal" in txt:
                color_font = color.red
            console.print(
                x=x + 1, y=y + 1 + i, string=f"{txt}", fg=color_font
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.KeySym.ESCAPE or event.sym == tcod.event.KeySym.RETURN:
            self.restart()

        elif event.sym == tcod.event.KeySym.BACKSPACE:
            self.on_quit()


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None
