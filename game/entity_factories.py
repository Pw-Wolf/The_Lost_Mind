from components.ai import HostileEnemy
from components.fighter import Fighter
from game.entity import Actor, Item
from components import consumable, equippable
from components.inventory import Inventory
from components.level import Level
from components.equipment import Equipment

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)

orc = Actor(
    char="o",
    color=(81, 130, 98),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=10),
)

troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=25),
)

goblin = Actor(
    char="G",
    color=(67, 39, 24),
    name="Goblin",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=8, base_defense=1, base_power=6),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=30),
)

health_potion = Item(
    char="!",
    color=(8, 80, 8),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
)

health_potion_big = Item(
    char="!",
    color=(10, 137, 10),
    name="Big Health Potion",
    consumable=consumable.HealingConsumable(amount=12),
)

lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)

confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)

fireball_scroll = Item(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)

poison_scroll = Item(
    char="~",
    color=(0, 255, 0),
    name="Posion Scroll",
    consumable=consumable.PosionConsumable(damage=4, number_of_turns=5),
)

freeze_scroll = Item(
    char="~",
    color=(0, 0, 255),
    name="Freeze Scroll",
    consumable=consumable.FreezeConsumable(number_of_turns=5),
)

dull_dagger = Item(
    char="/", color=(41, 21, 0), name="Dull Dagger", equippable=equippable.DullDagger()
)

dagger = Item(
    char="/", color=(87, 43, 0), name="Dagger", equippable=equippable.Dagger()
)

sharp_dagger = Item(
    char="/", color=(140, 71, 1), name="Sharp Dagger", equippable=equippable.SharpDagger()
)

dull_sword = Item(
    char="/", color=(89, 89, 89), name="Dull Sword", equippable=equippable.DullSword()
)

sword = Item(
    char="/", color=(117, 116, 116), name="Sword", equippable=equippable.Sword()
)

sharp_sword = Item(
    char="/", color=(189, 189, 189), name="Sharp Sword", equippable=equippable.SharpSword()
)

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatherArmor(),
)

chain_mail = Item(
    char="[",
    color=(117, 117, 117),
    name="Chain Mail",
    equippable=equippable.ChainMail()
)

iron_armor = Item(
    char="[",
    color=(212, 212, 212),
    name="Iron Armor",
    equippable=equippable.ChainMail()
)

diamond_armor = Item(
    char="[",
    color=(89, 233, 212),
    name="Diamond Armor",
    equippable=equippable.ChainMail()
)
