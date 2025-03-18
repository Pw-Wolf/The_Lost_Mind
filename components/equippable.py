from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from components.equipment_type import EquipmentType

if TYPE_CHECKING:
	from game.entity import Item


class Equippable(BaseComponent):
	parent: Item

	def __init__(
		self,
		equipment_type: EquipmentType,
		power_bonus: int = 0,
		defense_bonus: int = 0,
	):
		self.equipment_type = equipment_type

		self.power_bonus = power_bonus
		self.defense_bonus = defense_bonus

	# Daggers
class DullDagger(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=1.5)

class Dagger(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)

class SharpDagger(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2.5)

	# Swords
class DullSword(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=3.5)

class Sword(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)

class SharpSword(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=5)

	# Armors
class LeatherArmor(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)

class ChainMail(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)

class IronArmor(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=4)

class DiamondArmor(Equippable):
	def __init__(self) -> None:
		super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=5)