class Impossible(Exception):
	"""Exception raised when an action is impossible to be performed.

	The reason is given as the exception message.
	"""

class QuitWithoutSaving(SystemExit):
	"""Can be raised to exit the game without automatically saving."""

class Restart(SystemExit):
	"""Can be raised to restart the game without automatically leaving."""


class mainMenu(SystemExit):
	"""Can be raised to get to main Menu of the game."""

class saveSettings(SystemExit):
	"""Can be raised to get to main Menu of the game."""

class launchUpdate(SystemExit):
	"""Can be raised to close the game and open Update application"""

class DownloadError(Exception):
	"""Exception raised when an error occurs during downloading the update."""