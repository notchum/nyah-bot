import random
from enum import Enum
from typing import List


class TraitTypes(Enum):
    NONE                  = 0
    
    SILENT_STRIKE         = 1
    KI_CONTROL            = 2
    DRAGON_FIST           = 3
    IRON_BODY             = 4
    HONOR_BOUND           = 5

    TELEPORTATION         = 10
    SWORDSMANSHIP         = 11
    SPIRIT_FORM           = 12
    RASENGAN              = 13
    GENJUTSU_MASTERY      = 14

    ELEMENTAL_COMBINATION = 21
    MAGIC_AFFINITY        = 22
    BLADE_DANCER          = 23
    ILLUSIONIST           = 24
    EXCLUSIVE_CODE        = 25

    SUPER_SAIYAN          = 31
    DEATH_NOTE            = 32
    DIVINE_BLESSING       = 33
    DOMAIN_EXPANSION      = 34

class Trait:
    def __init__(self, type_: TraitTypes, callback_):
        self.type = type_
        self.callback = callback_
    
    def __str__(self):
        return f"- **__{self.type.name.replace('_', ' ').title()}__**\n"

# none_trait = Trait(
#     name="None",
#     trait_type=None,
#     trait_callback=None,
# )

# TRAITS = [
#     [
#         fire_affinity,
#         water_affinity,
#         wind_affinity,
#         shadow_walker,
#         silent_strike,
#         ki_control,
#         dragon_fist,
#         iron_body,
#         honor_bound,
#         courageous_heart,
#     ],
#     [
#         selective_element,
#         pyromancer,
#         teleportation,
#         swordsmanship,
#         archers_precision,
#         beast_form,
#         spirit_form,
#         rasengan,
#         genjutsu_mastery,
#     ],
#     [
#         elemental_combination,
#         magic_affinity,
#         blade_dancer,
#         beast_tamer,
#         illusionist,
#         exclusive_code,
#     ],
#     [
#         super_saiyan,
#         death_note,
#         divine_blessing,
#         domain_expansion,
#     ],
# ]

# def get_trait_group(trait_type: TraitTypes) -> List[CharacterTrait]:
#     return TRAITS[trait_type.value]

# def get_trait(trait_type: TraitTypes, trait_number: int) -> CharacterTrait:
#     if trait_number == None:
#         return none_trait
#     return TRAITS[trait_type.value][trait_number]

# class CharacterTraitDropper:
#     def __init__(self, user_level: int):
#         self.user_level = user_level

#         self.common_drop_chance = 50
#         self.uncommon_drop_chance = 30
#         self.rare_drop_chance = 15
#         self.legendary_drop_chance = 5

#     def __get_drop_chance(self, base_chance):
#         # Increase drop chance for better trait types based on user's level
#         trait_multiplier = 1 + (self.user_level // 5)
#         return base_chance * trait_multiplier

#     def drop_common_trait(self):
#         common_drop_chance = self.__get_drop_chance(self.common_drop_chance)
#         if random.randint(1, 100) <= common_drop_chance:
#             return random.choice(TRAITS[TraitTypes.COMMON.value])
#         return none_trait

#     def drop_uncommon_trait(self):
#         uncommon_drop_chance = self.__get_drop_chance(self.uncommon_drop_chance)
#         if random.randint(1, 100) <= uncommon_drop_chance:
#             return random.choice(TRAITS[TraitTypes.UNCOMMON.value])
#         return none_trait

#     def drop_rare_trait(self):
#         rare_drop_chance = self.__get_drop_chance(self.rare_drop_chance)
#         if random.randint(1, 100) <= rare_drop_chance:
#             return random.choice(TRAITS[TraitTypes.RARE.value])
#         return none_trait

#     def drop_legendary_trait(self):
#         legendary_drop_chance = self.__get_drop_chance(self.legendary_drop_chance)
#         if random.randint(1, 100) <= legendary_drop_chance:
#             return random.choice(TRAITS[TraitTypes.LEGENDARY.value])
#         return none_trait
