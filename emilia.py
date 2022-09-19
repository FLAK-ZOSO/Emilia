#!/usr/bin/env python3
import nextcord
from nextcord.ext.commands import Bot
from nextcord.activity import Activity, ActivityType
from nextcord.interactions import Interaction

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
async def write(ctx, *, text: str) -> None:
    await ctx.message.delete()
    await ctx.send(text)


@Emilia.slash_command(description="Tell me what to say...")
async def say(interaction: Interaction, text: str):
    await interaction.channel.send(text)


Emilia.run(open("token.txt").read())