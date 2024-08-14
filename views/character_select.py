import uuid

import disnake

from models import Harem, Claim
from helpers import Mongo

mongo = Mongo()

class CharacterDropdown(disnake.ui.StringSelect["CharacterSelectView"]):
    def __init__(self, characters: Harem):
        options = [
            disnake.SelectOption(label=character.name, value=str(character.id))
            for character in characters
        ]
        super().__init__(placeholder="Select one of your characters", options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        self.view.stop()
        choice = self.values[0]
        selected_character_id = uuid.UUID(choice)

        claim = await mongo.fetch_claim(selected_character_id)
        
        embed = disnake.Embed(
            description=f"Are you sure you want to select **__{claim.name}__**?",
            color=disnake.Color.greyple()
        )

        

        await inter.response.edit_message(
            embeds=[current_embed, embed],
            view=MarryDivorceView(
                claim=claim,
                embed=current_embed,
                author=self.author, 
                reference_view=self
            )
        )

        await inter.response.edit_message(f"You chose {choice}", view=None)

class CharacterSelectView(disnake.ui.View):
    message: disnake.Message

    def __init__(self, author: disnake.User | disnake.Member, characters: Harem):
        super().__init__()
        self.author = author

        self.add_item(CharacterDropdown(characters))

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

class CharacterConfirmView(disnake.ui.View):
    def __init__(self, claim: Claim, author: disnake.User | disnake.Member, reference_view: disnake.ui.View) -> None:
        super().__init__()
        self.claim = claim
        self.embed = embed
        self.author = author
        self.reference_view = reference_view

        for child in reference_view.children:
            if isinstance(child, disnake.ui.Button) and child.label in ["Marry", "Divorce"]:
                self.marry_divorce_button = child
                match self.marry_divorce_button.label:
                    case "Marry":
                        self.confirm.label="Confirm Marry?"
                        self.confirm.emoji=Emojis.STATE_MARRIED
                    case "Divorce":
                        self.confirm.label="Confirm Divorce?"
                        self.confirm.emoji=Emojis.STATE_UNMARRIED
                    case _:
                        logger.error(f"Invalid type: {self.type}")

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        return interaction.author.id == self.author.id

    @disnake.ui.button(style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        match self.marry_divorce_button.label:
            case "Marry":
                self.claim.marry()
                await mongo.update_claim(self.claim)
                
                self.embed.color = disnake.Color.green()
                status_field_index = next((i for i, field in enumerate(self.embed.fields) if field.name == "Status"), None)
                if status_field_index is not None:
                    self.embed.set_field_at(
                        index=status_field_index,
                        name="Status",
                        value=f"{Emojis.STATE_MARRIED} Married"
                    )

                self.marry_divorce_button.label = "Divorce"
                self.marry_divorce_button.emoji = Emojis.STATE_UNMARRIED

                waifu = await mongo.fetch_waifu(self.claim.slug)
                result_embed = disnake.Embed(
                    description=f"Married **__{waifu.name}__** {Emojis.STATE_MARRIED}",
                    color=disnake.Color.fuchsia()
                )
            case "Divorce":
                self.claim.divorce()
                await mongo.update_claim(self.claim)

                self.embed.color = disnake.Color.red()
                status_field_index = next((i for i, field in enumerate(self.embed.fields) if field.name == "Status"), None)
                if status_field_index is not None:
                    self.embed.set_field_at(
                        index=status_field_index,
                        name="Status",
                        value=f"{Emojis.STATE_UNMARRIED} Unmarried"
                    )
                
                self.marry_divorce_button.label = "Marry"
                self.marry_divorce_button.emoji = Emojis.STATE_MARRIED
                
                waifu = await mongo.fetch_waifu(self.claim.slug)
                result_embed = disnake.Embed(
                    description=f"Divorced **__{waifu.name}__** {Emojis.STATE_UNMARRIED}",
                    color=disnake.Color.dark_blue()
                )
            case _:
                logger.error(f"Invalid type: {self.type}")
                error_embed = ErrorEmbed("Something went wrong!")
                return await interaction.response.edit_message(
                    embed=error_embed,
                    view=None
                )
        
        await interaction.response.edit_message(
            embeds=[self.embed, result_embed],
            view=self.reference_view
        )

    @disnake.ui.button(label="Cancel", emoji="✖️", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.edit_message(embed=self.embed, view=self.reference_view)