import game.setup_game as setup_game
import core.input_handlers as input_handlers
import core.exceptions as exceptions
import core.color as color
import core.settings as settings
import tcod.sdl.audio
import tcod
import os
import sys
import logging
import traceback
from typing import Optional

sys.dont_write_bytecode = True


# Set up logging
log_file = f'{settings.data.path_folder}The_Lost_Mind.log'
logging.basicConfig(filename=log_file, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        logging.info("Game saved.")


def toggle_fullscreen(context: tcod.context.Context, fullscreen) -> None:
    """Set the window to fullscreen or windowed mode based on the fullscreen parameter."""
    if not context.sdl_window_p:
        return
    tcod.lib.SDL_SetWindowFullscreen(
        context.sdl_window_p,
        tcod.lib.SDL_WINDOW_FULLSCREEN_DESKTOP if fullscreen else 0,
    )


def load_tileset() -> Optional[tcod.tileset.Tileset]:
    """Load the tileset for the game."""
    try:
        return tcod.tileset.load_tilesheet(
            'assets/images/dejavu10x10_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD
        )
    except Exception as ex:
        logging.error(f"Failed to load tileset: {ex}")
        return None


def main() -> bool:
    tileset = load_tileset()
    if not tileset:
        return False
    # Set the initial window flags
    FLAGS = tcod.context.SDL_WINDOW_RESIZABLE | tcod.context.SDL_WINDOW_MAXIMIZED
    if settings.data_settings["fullscreen"]:
        FLAGS = tcod.context.SDL_WINDOW_RESIZABLE | tcod.context.SDL_WINDOW_FULLSCREEN_DESKTOP

    # Create a new terminal context with the specified settings
    with tcod.context.new_terminal(
        settings.data.screen_width,
        settings.data.screen_height,
        tileset=tileset,
        title="The Lost Mind",
        vsync=True,
        sdl_window_flags=FLAGS,
    ) as context:
        root_console = tcod.console.Console(settings.data.screen_width, settings.data.screen_height, order="F")
        toggle_fullscreen(context, settings.data_settings["fullscreen"])
        while True:
            # Set up the main menu handler
            handler: input_handlers.BaseEventHandler = setup_game.MainMenu()
            try:
                while True:
                    root_console.clear()
                    handler.on_render(console=root_console)
                    context.present(root_console)
                    try:
                        for event in tcod.event.wait():
                            context.convert_event(event)
                            handler = handler.handle_events(event)
                    except Exception:
                        logging.error("Exception occurred during event handling", exc_info=True)
                        if isinstance(handler, input_handlers.EventHandler):
                            handler.engine.message_log.add_message(traceback.format_exc(), color.error)
            except exceptions.Restart:
                pass
            except exceptions.DownloadError:
                print("Download Error")
            except exceptions.QuitWithoutSaving:
                raise
            except exceptions.launchUpdate:
                os.startfile(".\\assets\\manipulator.bat")
                raise
            except exceptions.saveSettings:
                input_handlers.player_controls()
                toggle_fullscreen(context, settings.data_settings["fullscreen"])
                settings.data.save_settings()
            except exceptions.mainMenu:
                save_game(handler, "savegame.sav")
            except SystemExit:
                save_game(handler, "savegame.sav")
                raise
            except BaseException:
                save_game(handler, "savegame.sav")
                raise


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.error("Exception occurred in main", exc_info=True)
