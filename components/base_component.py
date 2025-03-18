from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from core.engine import Engine
	from game.entity import Entity
	from game.game_map import GameMap


class BaseComponent:
	parent: Entity  # Owning entity instance.

	@property
	def gamemap(self) -> GameMap:
		return self.parent.gamemap

	@property
	def engine(self) -> Engine:
		return self.gamemap.engine
