from classes import *

# Players
crystia = Archer('Crystia')
ayame = Knight('Ayame')
yana = Cleric('Yana')


vane_of_arthropods = EquipItem('Vane of Arthropods', EquipSlot.WEAPON, Knight,
                               Upgrades(attack_power=1.5, speed=0.8))
pendant_of_valor = EquipItem('Pendant of Valor', EquipSlot.AMULET, Knight,
                             Upgrades(attack_power=1.5))
long_bow = EquipItem('Long Bow', 'weapon', Archer,
                     Upgrades(attack_power=2, speed=0.8))
ten_coins = Collectibles(10, 'c')
two_potions = Collectibles(2, 'p')

# First battle
print("Aquatic Spider and Swamp Spider block the way!")

spider1 = Enemy('Swamp Spider', Stats(max_health=20, attack_power=10, speed=5.5), (two_potions, long_bow))
spider2 = Enemy('Aquatic Spider', Stats(max_health=40, attack_power=20, speed=3), (ten_coins,))
spider3 = Enemy()

battle()

# Second battle
print("A gargantuan spider and a vase block the way!")

queen_spider = QueenSpider('Queen Spider', Stats(max_health=100, attack_power=50, speed=5),
                           (pendant_of_valor, vane_of_arthropods))
vase = Entity('Ornamented Vase', 20, (ten_coins, two_potions))

battle()

if Player.defeat == 0:
    while vase.health > 0:
        print("However, the ornamented vase still covers the path!")
        Player.interaction()

    print("The path to the caverns is now clear...")
