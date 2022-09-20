#!/usr/bin/env python3
import json
import os
import nextcord
from nextcord.ext.commands import Bot, Context, command, has_permissions
from nextcord import SlashOption
from nextcord.activity import Activity, ActivityType
from nextcord.interactions import Interaction
from nextcord.message import Message
from nextcord.embeds import Embed
from nextcord.colour import Color

print("Initializing Emilia...")
Emilia = Bot(
    command_prefix=("E)", "Emilia ", "EMILIA "),
    strip_after_prefix=True,
    description="Emilia is a paranoid and pro-Soviet bot",
    owner_id=797844636281995274,
    activity=Activity(type=ActivityType.listening, name="CCCP - Fedeli alla Linea"),
    status=nextcord.Status.online,
    intents=nextcord.Intents.all(),
)


@Emilia.event
async def on_ready() -> None:
    print(f"...({Emilia.user.name}#{Emilia.user.discriminator}) online")


@Emilia.command()
async def write(ctx: Context, *, text: str) -> None:
    await ctx.message.delete()
    await ctx.send(text)


@Emilia.slash_command(description="Tell me what to say...")
async def say(interaction: Interaction, text: str, embed: bool):
    if (embed):
        embed_ = Embed(title="And the Radio Says...", description=text, color=Color.red())
        embed_.set_footer(text=interaction.user.nick, icon_url=interaction.user.avatar)
        await interaction.channel.send(embed=embed_)
    else:
        await interaction.channel.send(text)
    await interaction.response.send_message("Message sent", ephemeral=True)


Emilia.run(open("token.txt").read())