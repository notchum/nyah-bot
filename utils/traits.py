import random
from enum import Enum
from typing import List

from utils.constants import Money

class TraitTypes(Enum):
    COMMON = 0
    UNCOMMON = 1
    RARE = 2
    LEGENDARY = 3

class StatModifiers(Enum):
    ATTACK_UP = 1
    ATTACK_DOWN = 2
    DEFENSE_UP = 3
    DEFENSE_DOWN = 4
    HEALTH_UP = 5
    HEALTH_DOWN = 6
    SPEED_UP = 7
    SPEED_DOWN = 8
    MAGIC_UP = 9
    MAGIC_DOWN = 10

class CharacterTrait:
    def __init__(self, name, trait_type, trait_number, modifiers):
        self.name = name
        self.trait_type = trait_type
        self.trait_number = trait_number
        self.modifiers = modifiers 

    def apply_modifiers(self, claim):
        for modifier, value in self.modifiers.items():
            value = value / 100
            if modifier == StatModifiers.ATTACK_UP:
                claim.attack_mod = int(value * claim.attack)
            elif modifier == StatModifiers.ATTACK_DOWN:
                claim.attack_mod = -int(value * claim.attack)
            elif modifier == StatModifiers.DEFENSE_UP:
                claim.defense_mod = int(value * claim.defense)
            elif modifier == StatModifiers.DEFENSE_DOWN:
                claim.defense_mod = -int(value * claim.defense)
            elif modifier == StatModifiers.HEALTH_UP:
                claim.health_mod = int(value * claim.health)
            elif modifier == StatModifiers.HEALTH_DOWN:
                claim.health_mod = -int(value * claim.health)
            elif modifier == StatModifiers.SPEED_UP:
                claim.speed_mod = int(value * claim.speed)
            elif modifier == StatModifiers.SPEED_DOWN:
                claim.speed_mod = -int(value * claim.speed)
            elif modifier == StatModifiers.MAGIC_UP:
                claim.magic_mod = int(value * claim.magic)
            elif modifier == StatModifiers.MAGIC_DOWN:
                claim.magic_mod = -int(value * claim.magic)
    
    @property
    def money_value(self):
        if self.trait_type == TraitTypes.COMMON:
            return Money.COMMON_TRAIT_PRICE.value
        elif self.trait_type == TraitTypes.UNCOMMON:
            return Money.UNCOMMON_TRAIT_PRICE.value
        elif self.trait_type == TraitTypes.RARE:
            return Money.RARE_TRAIT_PRICE.value
        elif self.trait_type == TraitTypes.LEGENDARY:
            return Money.LEGENDARY_TRAIT_PRICE.value
        return 0  # Unknown trait type
    
    def __str__(self):
        return f"- **__{self.name}__**\n" + \
                "\n".join([f"  - {modifier.name.replace('_', ' ').title()}: {value}%" for modifier, value in self.modifiers.items()])

none_trait = CharacterTrait(
    name="None",
    trait_type=None,
    trait_number=None,
    modifiers={}
)

##*************************************************##
##********          COMMON TRAITS           *******##
##*************************************************##

class CommonTraits(Enum):
    FIRE_AFFINITY = 0
    WATER_AFFINITY = 1
    WIND_AFFINITY = 2
    SHADOW_WALKER = 3
    SILENT_STRIKE = 4
    KI_CONTROL = 5
    DRAGON_FIST = 6
    IRON_BODY = 7
    HONOR_BOUND = 8
    COURAGEOUS_HEART = 9

fire_affinity = CharacterTrait(
    name="Fire Affinity",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.FIRE_AFFINITY.value,
    modifiers={
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.DEFENSE_DOWN: 5,
    }
)

water_affinity = CharacterTrait(
    name="Water Affinity",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.WATER_AFFINITY.value,
    modifiers={
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.HEALTH_DOWN: 5,
    }
)

wind_affinity = CharacterTrait(
    name="Wind Affinity",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.WIND_AFFINITY.value,
    modifiers={
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.ATTACK_DOWN: 5,
    }
)

shadow_walker = CharacterTrait(
    name="Shadow Walker",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.SHADOW_WALKER.value,
    modifiers={
        StatModifiers.SPEED_UP: 5,
        StatModifiers.ATTACK_DOWN: 5,
    }
)

silent_strike = CharacterTrait(
    name="Silent Strike",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.SILENT_STRIKE.value,
    modifiers={
        StatModifiers.ATTACK_UP: 10,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

ki_control = CharacterTrait(
    name="Ki Control",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.KI_CONTROL.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_DOWN: 5,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

dragon_fist = CharacterTrait(
    name="Dragon Fist",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.DRAGON_FIST.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

iron_body = CharacterTrait(
    name="Iron Body",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.IRON_BODY.value,
    modifiers={
        StatModifiers.DEFENSE_UP: 10,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.SPEED_DOWN: 10,
    }
)

honor_bound = CharacterTrait(
    name="Honor Bound",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.HONOR_BOUND.value,
    modifiers={
        StatModifiers.DEFENSE_UP: 10,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.ATTACK_DOWN: 5,
    }
)

courageous_heart = CharacterTrait(
    name="Courageous Heart",
    trait_type=TraitTypes.COMMON,
    trait_number=CommonTraits.COURAGEOUS_HEART.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.SPEED_DOWN: 5,
    }
)

##*************************************************##
##********         UNCOMMON TRAITS          *******##
##*************************************************##

class UncommonTraits(Enum):
    SELECTIVE_ELEMENT = 0
    PYROMANCER = 1
    TELEPORTATION = 2
    SWORDSMANSHIP = 3
    ARCHERS_PRECISION = 4
    BEAST_FORM = 5
    SPIRIT_FORM = 6
    RASENGAN = 7
    GENJUTSU_MASTERY = 8

selective_element = CharacterTrait(
    name="Selective Element",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.SELECTIVE_ELEMENT.value,
    modifiers={
        StatModifiers.DEFENSE_UP: 20,
        StatModifiers.SPEED_DOWN: 5,
    }
)

pyromancer = CharacterTrait(
    name="Pyromancer",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.PYROMANCER.value,
    modifiers={
        StatModifiers.ATTACK_UP: 20,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

teleportation = CharacterTrait(
    name="Teleportation",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.TELEPORTATION.value,
    modifiers={
        StatModifiers.SPEED_UP: 15,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

swordsmanship = CharacterTrait(
    name="Swordsmanship",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.SWORDSMANSHIP.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.SPEED_DOWN: 10,
    }
)

archers_precision = CharacterTrait(
    name="Archer's Precision",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.ARCHERS_PRECISION.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

beast_form = CharacterTrait(
    name="Beast Form",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.BEAST_FORM.value,
    modifiers={
        StatModifiers.ATTACK_UP: 10,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

spirit_form = CharacterTrait(
    name="Spirit Form",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.SPIRIT_FORM.value,
    modifiers={
        StatModifiers.SPEED_UP: 10,
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

rasengan = CharacterTrait(
    name="Rasengan",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.RASENGAN.value,
    modifiers={
        StatModifiers.ATTACK_UP: 10,
        StatModifiers.SPEED_UP: 5,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

genjutsu_mastery = CharacterTrait(
    name="Genjutsu Mastery",
    trait_type=TraitTypes.UNCOMMON,
    trait_number=UncommonTraits.GENJUTSU_MASTERY.value,
    modifiers={
        StatModifiers.ATTACK_UP: 10, # Evasion?
        StatModifiers.DEFENSE_UP: 5, # Confusion?
        StatModifiers.HEALTH_DOWN: 10,
    }
)

##*************************************************##
##********            RARE TRAITS           *******##
##*************************************************##

class RareTraits(Enum):
    ELEMENTAL_COMBINATION = 0
    MAGIC_AFFINITY = 1
    BLADE_DANCER = 2
    BEAST_TAMER = 3
    ILLUSIONIST = 4
    EXCLUSIVE_CODE = 5

elemental_combination = CharacterTrait(
    name="Elemental Combination",
    trait_type=TraitTypes.RARE,
    trait_number=RareTraits.ELEMENTAL_COMBINATION.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_UP: 10,
        StatModifiers.SPEED_DOWN: 10,
    }
)

magic_affinity = CharacterTrait(
    name="Magic Affinity",
    trait_type=TraitTypes.RARE,
    trait_number=RareTraits.MAGIC_AFFINITY.value,
    modifiers={
        StatModifiers.MAGIC_UP: 20,
        StatModifiers.SPEED_UP: 15,
        StatModifiers.HEALTH_DOWN: 15,
    }
)

blade_dancer = CharacterTrait(
    name="Blade Dancer",
    trait_type=TraitTypes.RARE,
    trait_number=RareTraits.BLADE_DANCER.value,
    modifiers={
        StatModifiers.SPEED_UP: 20,
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.HEALTH_DOWN: 15,
    }
)

beast_tamer = CharacterTrait(
    name="Beast Tamer",
    trait_type=TraitTypes.RARE,
    trait_number=RareTraits.BEAST_TAMER.value,
    modifiers={
        StatModifiers.HEALTH_UP: 15,
        StatModifiers.DEFENSE_UP: 15,
        StatModifiers.SPEED_DOWN: 15,
    }
)

illusionist = CharacterTrait(
    name="Illusionist",
    trait_type=TraitTypes.RARE,
    trait_number=RareTraits.ILLUSIONIST.value,
    modifiers={
        StatModifiers.SPEED_UP: 20,
        StatModifiers.DEFENSE_UP: 15,
        StatModifiers.ATTACK_DOWN: 15,
    }
)

exclusive_code = CharacterTrait(
    name="Exclusive Code",
    trait_type=TraitTypes.RARE,
    trait_number=RareTraits.EXCLUSIVE_CODE.value,
    modifiers={
        StatModifiers.SPEED_UP: 10,
        StatModifiers.DEFENSE_UP: 5,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.ATTACK_DOWN: 25,
    }
)

##*************************************************##
##********         LEGENDARY TRAITS         *******##
##*************************************************##

class LegendaryTraits(Enum):
    SUPER_SAIYAN = 0
    DEATH_NOTE = 1
    DIVINE_BLESSING = 2
    DOMAIN_EXPANSION = 3

super_saiyan = CharacterTrait(
    name="Super Saiyan",
    trait_type=TraitTypes.LEGENDARY,
    trait_number=LegendaryTraits.SUPER_SAIYAN.value,
    modifiers={
        StatModifiers.ATTACK_UP: 35,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.DEFENSE_DOWN: 20,
    }
)

death_note = CharacterTrait(
    name="Death Note",
    trait_type=TraitTypes.LEGENDARY,
    trait_number=LegendaryTraits.DEATH_NOTE.value,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.SPEED_UP: 10,
        StatModifiers.MAGIC_UP: 20,
        StatModifiers.DEFENSE_DOWN: 20,
    }
)

divine_blessing = CharacterTrait(
    name="Divine Blessing",
    trait_type=TraitTypes.LEGENDARY,
    trait_number=LegendaryTraits.DIVINE_BLESSING.value,
    modifiers={
        StatModifiers.MAGIC_UP: 15,
        StatModifiers.DEFENSE_UP: 15,
    }
)

domain_expansion = CharacterTrait(
    name="Domain Expansion",
    trait_type=TraitTypes.LEGENDARY,
    trait_number=LegendaryTraits.DOMAIN_EXPANSION.value,
    modifiers={
        StatModifiers.ATTACK_UP: 25,
        StatModifiers.MAGIC_UP: 20,
        StatModifiers.HEALTH_DOWN: 25,
    }
)


TRAITS = [
    [
        fire_affinity,
        water_affinity,
        wind_affinity,
        shadow_walker,
        silent_strike,
        ki_control,
        dragon_fist,
        iron_body,
        honor_bound,
        courageous_heart,
    ],
    [
        selective_element,
        pyromancer,
        teleportation,
        swordsmanship,
        archers_precision,
        beast_form,
        spirit_form,
        rasengan,
        genjutsu_mastery,
    ],
    [
        elemental_combination,
        magic_affinity,
        blade_dancer,
        beast_tamer,
        illusionist,
        exclusive_code,
    ],
    [
        super_saiyan,
        death_note,
        divine_blessing,
        domain_expansion,
    ],
]

def get_trait_group(trait_type: TraitTypes) -> List[CharacterTrait]:
    return TRAITS[trait_type.value]

def get_trait(trait_type: TraitTypes, trait_number: int) -> CharacterTrait:
    if trait_number == None:
        return none_trait
    return TRAITS[trait_type.value][trait_number]

class CharacterTraitDropper:
    def __init__(self, user_level: int):
        self.user_level = user_level

        self.common_drop_chance = 50
        self.uncommon_drop_chance = 30
        self.rare_drop_chance = 15
        self.legendary_drop_chance = 5

    def __get_drop_chance(self, base_chance):
        # Increase drop chance for better trait types based on user's level
        trait_multiplier = 1 + (self.user_level // 5)
        return base_chance * trait_multiplier

    def drop_common_trait(self):
        common_drop_chance = self.__get_drop_chance(self.common_drop_chance)
        if random.randint(1, 100) <= common_drop_chance:
            return random.choice(TRAITS[TraitTypes.COMMON.value])
        return none_trait

    def drop_uncommon_trait(self):
        uncommon_drop_chance = self.__get_drop_chance(self.uncommon_drop_chance)
        if random.randint(1, 100) <= uncommon_drop_chance:
            return random.choice(TRAITS[TraitTypes.UNCOMMON.value])
        return none_trait

    def drop_rare_trait(self):
        rare_drop_chance = self.__get_drop_chance(self.rare_drop_chance)
        if random.randint(1, 100) <= rare_drop_chance:
            return random.choice(TRAITS[TraitTypes.RARE.value])
        return none_trait

    def drop_legendary_trait(self):
        legendary_drop_chance = self.__get_drop_chance(self.legendary_drop_chance)
        if random.randint(1, 100) <= legendary_drop_chance:
            return random.choice(TRAITS[TraitTypes.LEGENDARY.value])
        return none_trait
