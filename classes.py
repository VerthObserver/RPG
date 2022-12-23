from __future__ import annotations
from random import choice, randint, uniform
from dataclasses import dataclass

item_dict = {}


class Collectibles:
    """Game collectibles."""

    def __init__(self, amount: int, col_type: str) -> None:
        if col_type == 'p':
            self.name = f"{amount} Potions"
        if col_type == 'c':
            self.name = f"{amount} Coins"
        self.amount = amount

        # Stores all instances into a dictionary by name.
        item_dict.update({str(self.name): self})

    def __str__(self) -> str:
        return self.name


@dataclass
class Stats:
    """PC and NPC statistics."""
    max_health: float = None
    attack_power: float = None
    speed: float = None
    healing_power: float = None

    def show_stats(self) -> None:
        """Prints each of the assigned statistics with a format."""
        for key in self.__dict__:
            if self.__dict__[key] is not None:
                stat = key.replace('_', ' ').title()
                print(f"{stat}: {self.__dict__[key]}")


@dataclass
class Upgrades(Stats):
    """Stats-multipliers for EquipItems."""

    def upgrade_stats(self, player: Player) -> None:
        """For each of the stats in Upgrades, increases Player's respective stats."""
        for key in self.__dict__:
            if self.__dict__[key] is not None:
                player.stats.__dict__[key] = round(player.stats.__dict__[key] * self.__dict__[key], 1)

    def downgrade_stats(self, player: Player) -> None:
        """For each of the stats in Upgrades, decreases Player's respective stats."""
        for key in self.__dict__:
            if self.__dict__[key] is not None:
                player.stats.__dict__[key] = round(player.stats.__dict__[key] / self.__dict__[key], 1)


# TODO: Not working when creating items.
class EquipSlot:
    """Available equipment slots for Player and Enemies."""
    WEAPON = 'weapon'
    ARMOR = 'armor'
    AMULET = 'amulet'


# TODO: Consider separating equip items into the available equipment slots.
class EquipItem:
    """Equippable items."""

    equip_dict = {}

    def __init__(self, name: str, equip_slot: str, for_class: Player.__class__, upgrades: Upgrades) -> None:
        self.name = name
        self.equip_slot = equip_slot
        self.for_class = for_class
        self.upgrades = upgrades

        # Stores all instances into a dictionary by name.
        EquipItem.equip_dict.update({str(self.name): self})
        item_dict.update({str(self.name): self})

    def __str__(self) -> str:
        return self.name


@dataclass
class Equipment:
    """Player and Enemies equipment."""

    def __init__(self, player: Player, *items):
        self.player = player
        self.weapon = None
        self.armor = None
        self.amulet = None
        for item in items:  # For each of the passed items, assigns the equipment slot to the item and upgrades stats.
            setattr(self, item.equip_slot, item)
            item.upgrades.upgrade_stats(self.player)

    def equip(self, item: EquipItem) -> None:
        """Equips items."""
        # If another item is equipped, it unequips it.
        if getattr(self, item.equip_slot) is not None:
            self.unequip(item.equip_slot)

        setattr(self, item.equip_slot, item)  # Assigns the item to its respective slot.
        Player.inventory.remove(item.name)  # Removes the item from the shared inventory.
        item.upgrades.upgrade_stats(self.player)  # Upgrades Player stats.

    def unequip(self, equip_slot: str) -> None:
        """Unequips items from a given slot."""
        item = getattr(self, equip_slot)
        if item is None:
            print('Nothing equipped!')
            return

        Player.inventory.append(item.name)  # Returns the item to the shared inventory.
        item.upgrades.downgrade_stats(self.player)  # Removes the upgrades given by the item.
        setattr(self, equip_slot, None)  # Sets the slot where item was to None.
        print(f'Unequipped {item}')

    def show_equipment(self) -> None:
        """Prints each of the equipped items with a format."""
        for key in self.__dict__:
            # Skips 'player' attribute.
            if key != 'player':
                item = key.title()
                print(f"{item}: {self.__dict__[key]}")


@dataclass
class Player:
    """Player's baseclass."""
    player_dict = {}  # Translate user inputs.
    player_list = []  # Build battle.
    num_of_players = 0  # Alive player counter.
    now_interacting = False
    in_battle = False
    defeat = False

    inventory = []  # Shared inventory.
    potions = 0
    coins = 0
    potions_power = 20

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.stats: Stats = Stats()
        self.equipment: Equipment = Equipment(self)  # All slots are None by default.
        self.health: float = self.stats.max_health
        self.kills: int = 0
        self.can_act: int = 0  # As long as == 1, player will perform actions. next_player sets it to 0 outside battle.

        Player.player_dict.update({str(self.name): self})
        Player.player_list.append(self)
        Player.num_of_players += 1

    def action_identifier(self, action: str) -> None:
        """Identifies each of the user-inputted actions."""
        match action.split(maxsplit=1):
            case ['attack', target]:
                self.user_attack(target)
            case ['heal', target]:
                self.user_potions(target)
            case ['inventory']:
                Player.user_show_inventory()
            case ['equipment', target]:
                Player.user_show_equipment(target)
            case ['stats', target]:
                Player.user_show_stats(target)
            case ['pick up', item]:
                Player.user_pickup_item(item)
            case ['loot', target]:
                self.user_loot(target)
            case ['equip']:
                self.user_equip()
            case ['unequip']:
                self.user_unequip()
            case ['change']:
                self.user_change_player()
            case ['continue']:
                self.user_continue()
            case _:
                print('Unknown action')

    def user_actions(self) -> None:
        """Takes in user's inputs to decide the Player's action."""
        if self.health <= 0:
            return

        if Player.in_battle:
            self.can_act += 1
        # If the Player is in battle can_act should be <= 1.
        # If this is not the case, the Player has been immobilized (from the environment or an Enemy).
        if self.can_act <= 0 and Player.in_battle:
            print(f'{self.name} is immobilized!')
            return

        # Passive actions do not diminish can_act, allowing the player to perform another action.
        while self.can_act >= 1:
            action = input('Action: ')
            self.action_identifier(action)

    def damage(self, dmg: float, source: Enemy | Player) -> None:
        """Runs whenever the Player takes damage."""
        # Player has a probability to dodge the attack.
        if dodged(self.stats.speed, source.stats.speed):
            print(f'{self.name} has dodged the attack!')
            return

        self.health = round(self.health - dmg, 1)
        print(f'{self.name} has taken {dmg} points of damage from {source.name}. Remaining health: {self.health}')

        if self.health <= 0:
            Player.num_of_players -= 1  # Decreases the number of players alive.
            print(f'{self.name} has been incapacitated! '
                  f'{Player.num_of_players} party members remaining')
            if Player.num_of_players == 0:
                Player.defeat = True
                print(f'All party members incapacitated!')

    def attack(self, target: Entity | Enemy | Player, dmg: float) -> None:
        """Player's attack."""
        target.damage(dmg, self)

    def user_attack(self, target: str) -> None:
        """Attacks a target by self's attack power. Active.'"""
        # First, tries to attack an entity.
        try:
            target = Entity.ent_dict[target]
            attacked_player = False
        except KeyError:
            # If this is not possible, it attacks a player.
            # Assigning attacked_player = True so we can print a special message.
            try:
                target = Player.player_dict[target]
                attacked_player = True
            except KeyError:
                print('Unknown target')
                return

        if target.health <= 0:
            print(f"{target.name} is already dead!")
            return

        self.attack(target, self.stats.attack_power)
        if attacked_player:  # Special message.
            print(f'{target.name} says: What the hell, {self.name}!')
        if Player.in_battle:
            self.can_act -= 1

    @staticmethod
    def heal(target: Player, amount: float) -> None:
        """Heal a specific target."""
        past_health = target.health
        target.health += amount
        # Increases number of players alive if the player was dead and now is not.
        if past_health <= 0 < target.health:
            Player.num_of_players += 1

        # Health can't be greater than max_health. If this happens, health is set to max_health.
        if target.health > target.stats.max_health:
            target.health = target.stats.max_health
        print(f'Healed {amount} HP to {target.name}. Current health: {target.health}')

    def user_potions(self, target: str) -> None:
        """Allows user to use a potion to heal a player. Active."""
        if Player.potions == 0:
            print('No potions left!')
            return
        try:
            target = Player.player_dict[target]
        except KeyError:
            print('Unknown player')
            return
        if target.health == target.stats.max_health:
            print('Already full health!')
            return

        Player.potions -= 1
        Player.heal(target, Player.potions_power)
        if Player.in_battle:
            self.can_act -= 1

    @staticmethod
    def user_show_equipment(player: str) -> None:
        """Given a user-selected player, shows equipment of player. Passive."""
        try:
            player = Player.player_dict[player]
        except KeyError:
            print('Unknown player')
            return

        print(f"\n{player.name}\'s Inventory:")
        player.equipment.show_equipment()

    @staticmethod
    def user_show_inventory() -> None:
        """Shows shared inventory. Passive."""
        print(f"\nShared Inventory:"
              f"\nBag of holding: {Player.inventory}"
              f"\nPotions: {Player.potions}"
              f"\nCoins: {Player.coins}\n")

    @staticmethod
    def user_show_stats(player: str) -> None:
        """Given a user-selected player, shows statistics of player. Passive."""
        try:
            player = Player.player_dict[player]
        except KeyError:
            print('Unknown player')
            return

        print(f"\n{player.name}\'s Stats:"
              f"\n-----------------")
        player.stats.show_stats()

    @staticmethod
    def pickup_item(item) -> None:  # TODO: Abstract item class.
        """Picks up an item. Adds coins and potions to class variables."""
        match item.name.split():
            case [amount, 'Coins']:
                Player.coins += int(amount)
            case [amount, 'Potions']:
                Player.potions += int(amount)
            case _:
                Player.inventory.append(item.name)
        item_dict.pop(item.name)  # Removes item from dictionary so that it can only be picked up once.

    @staticmethod
    def user_pickup_item(item: str) -> None:
        """Picks up a user-selected item. Active."""
        try:
            item = item_dict[item]
        except KeyError:
            print(f'Cannot pickup {item.name}')
            return
        print(f'Picked up {item.name}!')

    @staticmethod
    def loot(target: Entity | Enemy) -> None:
        """Loots a target's inventory. Adds coins and potions to class variables."""
        for item in target.inventory:
            Player.pickup_item(item)
            print(f'Picked up {item.name} from {target}!')
        target.inventory = []

    def user_loot(self, entity: Entity | Enemy) -> None:
        """Loots a user-selected entity's inventory. Adds coins and potions to class variables. Active."""
        try:
            entity = Entity.ent_dict[entity]
        except KeyError:
            print('Unknown target')
            return
        if entity.health > 0:
            print(f'Can\'t loot {entity.name} just yet!')
            return

        self.loot(entity)
        if Player.in_battle:
            self.can_act -= 1

    def user_equip(self) -> None:
        """
        If in battle, equips a user-selected item to self.
        If not in battle, equips a user-selected item to a user-selected Player.
        Passive.
        """
        if Player.in_battle:
            print(f'Equipping to {self.name}...')
            target = self
            item = input('Item: ')
        else:
            item = input('Equip: ')
            target = input('To: ')
            try:
                target = Player.player_dict[target]
            except KeyError:
                print('Unknown player')
                return

        try:
            item = EquipItem.equip_dict[item]
        except KeyError:
            print('Item does not exist!')
            return

        if not (item.name in Player.inventory):
            print('Item not in inventory!')
        elif not (isinstance(target, item.for_class)):
            print(f'Can only equip {item.name} to {item.for_class.__name__} class')
        else:
            target.equipment.equip(item)
            print(f'{item.name} equipped!')

    def user_unequip(self) -> None:
        """
        If in battle, unequips from self the item in a user-selected slot.
        If not in battle, unequips from a user-selected Player the item in a user-selected slot.
        Passive.
        """
        if Player.in_battle:
            print(f'Unequiping from {self.name}...')
            target = self
            slot = input('Unequip [slot of equipment]: ').lower()
        else:
            slot = input('Unequip [slot of equipment]: ').lower()
            target = input('From: ')
            try:
                target = Player.player_dict[target]
            except KeyError:
                print('Unknown player')
                return
        try:
            target.equipment.unequip(slot)
        except AttributeError:
            print('Unknown slot.')

    @staticmethod
    def revive_all() -> None:
        """Revives all dead players with a third of their max_health."""
        for player in Player.player_list:
            if player.health <= 0:
                player.health = player.stats.max_health / 3
                print(f'{player.name} has recuperated!')

    @staticmethod
    def interaction() -> None:
        """Players are now outside of battle. Any player is able to act until continue is called."""
        Player.in_battle = False
        Player.now_interacting = True
        while Player.now_interacting:
            player = input('\nSelect a player: ')
            try:
                player = Player.player_dict[player]
            except KeyError:
                print('Unknown player')
                continue
            print(f'\n{player.name}\'s actions:')
            # We set can_act to 1. While there are no turns outside of battle, players could be immobilized.
            player.can_act = 1
            player.user_actions()

    def user_change_player(self) -> None:
        """Allows user to change player outside of battle."""
        if Player.in_battle:
            print('Cannot change players in battle.')
        else:
            self.can_act = 0

    def user_continue(self) -> None:
        """Used outside of battle. Ends interaction."""
        # TODO: Should only be ended if they're not endangered. Trapped.
        if not Player.in_battle:
            Player.now_interacting = False
        self.can_act = 0

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name})'

    def __str__(self):
        return f'{self.name}, the {self.__class__.__name__}'


class Archer(Player):
    """Archer subclass."""

    def __init__(self, name: str):
        super().__init__(name)
        self.stats = Stats(max_health=80, attack_power=12, speed=5)
        self.equipment = Equipment(self, simple_bow)
        self.health = self.stats.max_health
        Player.potions += 6

    def user_triple_attack(self) -> None:
        """Attacks three targets with a sixth of Archer's attack_power."""
        light_atk = round(int(self.stats.attack_power / 6), 1)
        target1, target2, target3 = input('Target 1: '), input('Target 2: '), input('Target 3: ')

        try:
            target1, target2, target3 = Entity.ent_dict[target1], Entity.ent_dict[target2], Entity.ent_dict[target3]
        except KeyError:
            print('Unknown targets!')
            return

        # Will not waste an action if all enemies are dead.
        if target1.health <= 0 and target1.health <= 0 and target1.health <= 0:
            print('All targets already dead!')
            return

        self.attack(target1, light_atk)
        self.attack(target2, light_atk)
        self.attack(target3, light_atk)
        if Player.in_battle:
            self.can_act -= 1

    def action_identifier(self, action: str) -> None:
        """Action identifier. Added 'triple' for user_triple_attack."""
        match action.split(maxsplit=1):
            case ['triple']:
                self.user_triple_attack()
            case _:
                Player.action_identifier(self, action)


class Knight(Player):
    """Knight subclass."""

    def __init__(self, name: str):
        super().__init__(name)
        self.stats = Stats(max_health=100, attack_power=15, speed=5)
        self.equipment = Equipment(self, long_sword, curiass)
        self.health = self.stats.max_health
        self.protecting = None
        Player.potions += 1

    def user_defend(self) -> None:
        """The next attack is guaranteed to fall on self."""
        Player.player_list, self.protecting = [self], Player.player_list
        if Player.in_battle:
            self.can_act -= 1

    def damage(self, dmg: float, source: Enemy | Player) -> None:
        """Knight damage method. Cancels defend method."""
        super().damage(dmg, source)
        if self.protecting is not None:
            Player.player_list, self.protecting = self.protecting, None

    def action_identifier(self, action: str) -> None:
        """Action identifier. Added 'defend' for user_defend."""
        match action.split(maxsplit=1):
            case ['defend']:
                self.user_defend()
            case _:
                Player.action_identifier(self, action)


class Cleric(Player):

    def __init__(self, name: str):
        super().__init__(name)
        self.stats = Stats(max_health=60, attack_power=5, speed=5, healing_power=5)
        self.equipment = Equipment(self, book_of_secrets, curiass, crown_of_life)
        self.health = self.stats.max_health
        Player.potions += 1

    def user_purify(self) -> None:
        """When in battle, heals each of the Players by self's healing power."""
        if not Player.in_battle:
            print(f'{self.name}\'s Purify can only be used in battle')
            return

        for player in Player.player_list:
            if player.health == player.stats.max_health:
                print(f'{player.name} is already full health!')
                continue
            Player.heal(player, self.stats.healing_power)
            self.can_act = 0

    def action_identifier(self, action: str) -> None:
        """Action identifier. Added 'purify' for user_purify."""
        match action.split(maxsplit=1):
            case ['purify']:
                self.user_purify()
            case _:
                Player.action_identifier(self, action)


class Entity:
    """Class for environment objects with inventory."""
    ent_dict = {}  # Translate user inputs.
    ent_list = []  # TODO: Build environment? Still no use.

    def __init__(self, name: str, health: int, inventory: tuple = ()):
        self.name = name
        self.health = health
        self.inventory = inventory

        Entity.ent_dict.update({str(self.name): self})
        Entity.ent_list.append(self)

    def damage(self, dmg: float, source: Enemy | Player) -> None:
        """Runs whenever self takes damage."""
        self.health = round(self.health - dmg, 1)
        print(f'{self.name} has taken {dmg} points of damage from {source.name}. Remaining durability: {self.health}')
        if self.health <= 0:
            print(f'{self.name} has been broken!')

    def __repr__(self):
        return f"Entity({self.name}, {self.health}, {self.inventory})"

    def __str__(self):
        return self.name
    # TODO: When deleted, remove from dictionary


class Enemy:
    """Enemy baseclass."""
    enemy_list = []  # Build battle.
    num_of_enemies = 0  # Number of alive enemies.
    defeat = False

    def __init__(self, name: str, stats: Stats = Stats(max_health=1, attack_power=1, speed=1), inventory: tuple = ()):
        self.name = name
        self.stats = stats
        self.health = stats.max_health
        self.inventory = inventory

        # TODO: Are two different dicts necessary? For now, ent_dict suffices.
        Entity.ent_dict.update({str(self.name): self})
        Entity.ent_list.append(self)
        Enemy.enemy_list.append(self)
        Enemy.num_of_enemies += 1
        Enemy.defeat = False

    def attack(self, target: Player | Entity | Enemy) -> None:
        if self.health <= 0:
            return
        target.damage(self.stats.attack_power, self)

    def damage(self, dmg: float, source: Enemy | Player) -> None:
        """Runs whenever self takes damage."""
        if isinstance(source, Player):
            if dodged(self.stats.speed, source.stats.speed):
                print(f'{source.name} missed!')
                return
        self.health = round(self.health - dmg, 1)
        print(f'{self.name} has taken {dmg} points of damage from {source.name}. Remaining health: {self.health}')

        if self.health <= 0:
            Enemy.num_of_enemies -= 1  # Subtracts from the number of alive enemies.
            print(f'{self.name} has been killed! '
                  f'{Enemy.num_of_enemies} enemies remaining')
            if Enemy.num_of_enemies == 0:
                print('\nVictory!\n')
                # Loots all enemies.
                for enemy in Enemy.enemy_list:
                    Player.loot(enemy)

                # Removes all enemies from dicts.
                Enemy.enemy_dict = {}
                Enemy.enemy_list = []
                Enemy.defeat = True

    def __repr__(self):
        return f"Enemy({self.name}, {self.stats}, {self.inventory})"

    def __str__(self):
        return self.name


# TODO: Create special enemies.
class QueenSpider(Enemy):
    """Queen Spider subclass."""

    def __init__(self, name: str, stats: Stats = Stats(max_health=1, attack_power=1, speed=1), inventory: tuple = ()):
        super().__init__(name, stats, inventory)

    @staticmethod
    def paralyze(target: Player) -> None:
        """Paralyzes Player for three turns."""
        target.can_act = -3
        print(f'Queen Spider has spewed cobwebs! {target.name} is paralyzed for 3 turns!')

    def __repr__(self):
        return super().__repr__() + f' Special method: {self.paralyze}'


def dodged(self_speed: float, source_speed: float = None) -> bool:
    """Determines through a uniform distribution whether self dodged the attack."""
    # TODO: Traps.
    if source_speed is not None:
        dodge_coefficient = round((self_speed - source_speed) / self_speed, 2)
        return uniform(-0.75, dodge_coefficient) >= 0


def battle() -> None:
    """Starts a battle between current players and enemies."""
    Player.in_battle = True
    characters = Player.player_list + Enemy.enemy_list
    # Orders characters on descending order based on their speed.
    characters.sort(key=lambda char: char.stats.speed, reverse=True)
    num_of_rounds = 1

    # Until all players or all enemies are defeated.
    while not Player.defeat and not Enemy.defeat:
        print(f'\nRound {num_of_rounds}!')

        for character in characters:
            if Player.defeat or Enemy.defeat:
                break
            input()
            print(f'\n{character.name}\'s Turn!')

            if character.health <= 0:
                print(f'\n{character.name} is incapacitated!')
                continue

            if isinstance(character, Player):
                character.user_actions()
            if isinstance(character, Enemy):
                # Chooses a random alive player target.
                target = choice(Player.player_list)
                while target.health <= 0:
                    target = choice(Player.player_list)
                # TODO: Generalize.
                # If the enemy is a QueenSpider, it has a probability to paralyze the Player instead of attacking it.
                if isinstance(character, QueenSpider) and randint(0, 3) == 1:
                    character.paralyze(target)
                else:
                    character.attack(target)

        num_of_rounds += 1

    if Player.defeat:
        print('\nDefeat...')
    else:
        Player.revive_all()
    Player.interaction()
    input()


# Base items.
simple_bow = EquipItem('Simple Bow', EquipSlot.WEAPON, Archer, Upgrades(speed=1.3))
long_sword = EquipItem('Long Sword', EquipSlot.WEAPON, Knight, Upgrades(attack_power=1.2, speed=0.9))
curiass = EquipItem('Curiass', EquipSlot.ARMOR, Player, Upgrades(max_health=1.2, speed=0.65))
book_of_secrets = EquipItem('Book of Secrets', EquipSlot.WEAPON, Cleric, Upgrades(attack_power=1.75, speed=1.25))
crown_of_life = EquipItem('Crown of Life', EquipSlot.AMULET, Cleric, Upgrades(healing_power=2))
