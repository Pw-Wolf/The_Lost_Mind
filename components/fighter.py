from __future__ import annotations

# from json import loads
from typing import TYPE_CHECKING

import core.color as color
import core.input_handlers as input_handlers
import core.settings as settings
from components.base_component import BaseComponent
from components.scoreboard import send_score
from core.render_order import RenderOrder

if TYPE_CHECKING:
	from game.entity import Actor


class Fighter(BaseComponent):
	parent: Actor

	def __init__(self, hp: int, base_defense: int, base_power: int):
		self.max_hp = hp
		self._hp = hp
		self.base_defense = base_defense
		self.base_power = base_power
		self.default_base_power = base_power
		self.default_base_defense = base_defense
		self.default_max_hp = hp
		

	@property
	def hp(self) -> int:
		return self._hp

	@hp.setter
	def hp(self, value: int) -> None:
		self._hp = max(0, min(value, self.max_hp))
		if self._hp == 0 and self.parent.ai:
			self.die()

	@property
	def defense(self) -> int:
		return self.base_defense + self.defense_bonus

	@property
	def power(self) -> int:
		return self.base_power + self.power_bonus

	@property
	def defense_bonus(self) -> int:
		if self.parent.equipment:
			return self.parent.equipment.defense_bonus
		else:
			return 0

	@property
	def power_bonus(self) -> int:
		if self.parent.equipment:
			return self.parent.equipment.power_bonus
		else:
			return 0
		
	def send_to_scoreboard(self) -> None:
		name = settings.data_settings["name"]
		score = int(sum([i * 150 + (bool(i) * 350) for i in range(self.engine.player.level.current_level-1)]) + self.engine.player.level.current_xp + (bool(self.engine.player.level.current_level) * 350))
		send_score(score, name)
		
	def open_scoreboard(self):
		return input_handlers.PopupMessage(self, text="score") 


	def die(self) -> None:

		self.parent.char = "%"
		self.parent.color = (191, 0, 0)
		self.parent.blocks_movement = False
		self.parent.ai = None
		self.parent.name = f"remains of {self.parent.name}"
		self.parent.render_order = RenderOrder.CORPSE


		self.engine.player.level.add_xp(self.parent.level.xp_given)

		if self.engine.player is self.parent:
			death_message = "You died!"
			death_message_color = color.player_die
			self.send_to_scoreboard()
			self.open_scoreboard()

		else:
			death_message = f"{self.parent.name} is dead!"
			death_message_color = color.enemy_die

		self.engine.message_log.add_message(death_message, death_message_color)


	def heal(self, amount: int) -> int:
		if self.hp == self.max_hp:
			return 0

		new_hp_value = self.hp + amount

		if new_hp_value > self.max_hp:
			new_hp_value = self.max_hp

		amount_recovered = new_hp_value - self.hp

		self.hp = new_hp_value

		return amount_recovered

	def take_damage(self, amount: int) -> None:
		self.hp -= amount
