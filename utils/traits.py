import random
from enum import Enum

from models import Claim
from utils import Money

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
    def __init__(self, name, trait_type, modifiers):
        self.name = name
        self.trait_type = trait_type
        self.modifiers = modifiers 

    def apply_modifiers(self, claim: Claim):
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

##*************************************************##
##********          COMMON TRAITS           *******##
##*************************************************##

fire_affinity = CharacterTrait(
    name="Fire Affinity",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.DEFENSE_DOWN: 5,
    }
)

water_affinity = CharacterTrait(
    name="Water Affinity",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.HEALTH_DOWN: 5,
    }
)

wind_affinity = CharacterTrait(
    name="Wind Affinity",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.ATTACK_DOWN: 5,
    }
)

shadow_walker = CharacterTrait(
    name="Shadow Walker",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.SPEED_UP: 5,
        StatModifiers.ATTACK_DOWN: 5,
    }
)

silent_strike = CharacterTrait(
    name="Silent Strike",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 10,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

ki_control = CharacterTrait(
    name="Ki Control",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_DOWN: 5,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

dragon_fist = CharacterTrait(
    name="Dragon Fist",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

iron_body = CharacterTrait(
    name="Iron Body",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.DEFENSE_UP: 10,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.SPEED_DOWN: 10,
    }
)

honor_bound = CharacterTrait(
    name="Honor Bound",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.DEFENSE_UP: 10,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.ATTACK_DOWN: 5,
    }
)

courageous_heart = CharacterTrait(
    name="Courageous Heart",
    trait_type=TraitTypes.COMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.SPEED_DOWN: 5,
    }
)

##*************************************************##
##********         UNCOMMON TRAITS          *******##
##*************************************************##

selective_element = CharacterTrait(
    name="Selective Element",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.DEFENSE_UP: 20,
        StatModifiers.SPEED_DOWN: 5,
    }
)

pyromancer = CharacterTrait(
    name="Pyromancer",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 20,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

teleportation = CharacterTrait(
    name="Teleportation",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.SPEED_UP: 15,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

swordsmanship = CharacterTrait(
    name="Swordsmanship",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.SPEED_DOWN: 10,
    }
)

archers_precision = CharacterTrait(
    name="Archer's Precision",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

beast_form = CharacterTrait(
    name="Beast Form",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 10,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

spirit_form = CharacterTrait(
    name="Spirit Form",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.SPEED_UP: 10,
        StatModifiers.MAGIC_UP: 10,
        StatModifiers.HEALTH_DOWN: 10,
    }
)

rasengan = CharacterTrait(
    name="Rasengan",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 10,
        StatModifiers.SPEED_UP: 5,
        StatModifiers.DEFENSE_DOWN: 10,
    }
)

genjutsu_mastery = CharacterTrait(
    name="Genjutsu Mastery",
    trait_type=TraitTypes.UNCOMMON,
    modifiers={
        StatModifiers.ATTACK_UP: 10, # Evasion?
        StatModifiers.DEFENSE_UP: 5, # Confusion?
        StatModifiers.HEALTH_DOWN: 10,
    }
)

##*************************************************##
##********            RARE TRAITS           *******##
##*************************************************##

elemental_combination = CharacterTrait(
    name="Elemental Combination",
    trait_type=TraitTypes.RARE,
    modifiers={
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.DEFENSE_UP: 10,
        StatModifiers.SPEED_DOWN: 10,
    }
)

magic_affinity = CharacterTrait(
    name="Magic Affinity",
    trait_type=TraitTypes.RARE,
    modifiers={
        StatModifiers.MAGIC_UP: 20,
        StatModifiers.SPEED_UP: 15,
        StatModifiers.HEALTH_DOWN: 15,
    }
)

blade_dancer = CharacterTrait(
    name="Blade Dancer",
    trait_type=TraitTypes.RARE,
    modifiers={
        StatModifiers.SPEED_UP: 20,
        StatModifiers.ATTACK_UP: 15,
        StatModifiers.HEALTH_DOWN: 15,
    }
)

beast_tamer = CharacterTrait(
    name="Beast Tamer",
    trait_type=TraitTypes.RARE,
    modifiers={
        StatModifiers.HEALTH_UP: 15,
        StatModifiers.DEFENSE_UP: 15,
        StatModifiers.SPEED_DOWN: 15,
    }
)

illusionist = CharacterTrait(
    name="Illusionist",
    trait_type=TraitTypes.RARE,
    modifiers={
        StatModifiers.SPEED_UP: 20,
        StatModifiers.DEFENSE_UP: 15,
        StatModifiers.ATTACK_DOWN: 15,
    }
)

exclusive_code = CharacterTrait(
    name="Exclusive Code",
    trait_type=TraitTypes.RARE,
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

super_saiyan = CharacterTrait(
    name="Super Saiyan",
    trait_type=TraitTypes.LEGENDARY,
    modifiers={
        StatModifiers.ATTACK_UP: 35,
        StatModifiers.HEALTH_UP: 10,
        StatModifiers.DEFENSE_DOWN: 20,
    }
)

death_note = CharacterTrait(
    name="Death Note",
    trait_type=TraitTypes.LEGENDARY,
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
    modifiers={
        StatModifiers.MAGIC_UP: 15,
        StatModifiers.DEFENSE_UP: 15,
    }
)

domain_expansion = CharacterTrait(
    name="Domain Expansion",
    trait_type=TraitTypes.LEGENDARY,
    modifiers={
        StatModifiers.ATTACK_UP: 25,
        StatModifiers.MAGIC_UP: 20,
        StatModifiers.HEALTH_DOWN: 25,
    }
)

class CharacterTraitsCommon:
    @classmethod
    def get_traits(cls):
        return [
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
        ]
    
    @classmethod
    def get_trait_by_name(cls, trait_name):
        for trait in cls.get_traits():
            if trait.name == trait_name:
                return trait
        return None
    
    @classmethod
    def __str__(cls):
        return "\n".join([str(trait) for trait in cls.get_traits()])

class CharacterTraitsUncommon:
    @classmethod
    def get_traits(cls):
        return [
            selective_element,
            pyromancer,
            teleportation,
            swordsmanship,
            archers_precision,
            beast_form,
            spirit_form,
            rasengan,
            genjutsu_mastery,
        ]
    
    @classmethod
    def get_trait_by_name(cls, trait_name):
        for trait in cls.get_traits():
            if trait.name == trait_name:
                return trait
        return None
    
    @classmethod
    def __str__(cls):
        return "\n".join([str(trait) for trait in cls.get_traits()])

class CharacterTraitsRare:
    @classmethod
    def get_traits(cls):
        return [
            elemental_combination,
            magic_affinity,
            blade_dancer,
            beast_tamer,
            illusionist,
            exclusive_code,
        ]
    
    @classmethod
    def get_trait_by_name(cls, trait_name):
        for trait in cls.get_traits():
            if trait.name == trait_name:
                return trait
        return None
    
    @classmethod
    def __str__(cls):
        return "\n".join([str(trait) for trait in cls.get_traits()])

class CharacterTraitsLegendary:
    @classmethod
    def get_traits(cls):
        return [
            super_saiyan,
            death_note,
            divine_blessing,
            domain_expansion,
        ]
    
    @classmethod
    def get_trait_by_name(cls, trait_name):
        for trait in cls.get_traits():
            if trait.name == trait_name:
                return trait
        return None
    
    @classmethod
    def __str__(cls):
        return "\n".join([str(trait) for trait in cls.get_traits()])

class CharacterTraitDropper:
    def __init__(self, user_level: int):
        self.user_level = user_level

        self.common_drop_chance = 50
        self.uncommon_drop_chance = 30
        self.rare_drop_chance = 15
        self.legendary_drop_chance = 5

    def get_drop_chance(self, base_chance):
        # Increase drop chance for better trait types based on user's level
        trait_multiplier = 1 + (self.user_level // 5)
        return base_chance * trait_multiplier

    def drop_common_trait(self):
        common_drop_chance = self.get_drop_chance(self.common_drop_chance)
        if random.randint(1, 100) <= common_drop_chance:
            common_traits = CharacterTraitsCommon.get_traits()
            return random.choice(common_traits)
        return None

    def drop_uncommon_trait(self):
        uncommon_drop_chance = self.get_drop_chance(self.uncommon_drop_chance)
        if random.randint(1, 100) <= uncommon_drop_chance:
            uncommon_traits = CharacterTraitsUncommon.get_traits()
            return random.choice(uncommon_traits)
        return None

    def drop_rare_trait(self):
        rare_drop_chance = self.get_drop_chance(self.rare_drop_chance)
        if random.randint(1, 100) <= rare_drop_chance:
            rare_traits = CharacterTraitsRare.get_traits()
            return random.choice(rare_traits)
        return None

    def drop_legendary_trait(self):
        legendary_drop_chance = self.get_drop_chance(self.legendary_drop_chance)
        if random.randint(1, 100) <= legendary_drop_chance:
            legendary_traits = CharacterTraitsLegendary.get_traits()
            return random.choice(legendary_traits)
        return None

    def roll_all_traits(self):
        traits = {
            "common": self.drop_common_trait(),
            "uncommon": self.drop_uncommon_trait(),
            "rare": self.drop_rare_trait(),
            "legendary": self.drop_legendary_trait(),
        }
        return traits
