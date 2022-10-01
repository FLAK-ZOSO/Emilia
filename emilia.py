#!/usr/bin/env python3
import json
import os
import nextcord
from nextcord.ext.commands import Bot, Context, command, has_permissions
from nextcord import SlashOption, User, Member
from nextcord.activity import Activity, ActivityType
from nextcord.interactions import Interaction
from nextcord.message import Message
from nextcord.embeds import Embed
from nextcord.colour import Color
from nextcord.ext.commands.errors import MissingPermissions
from nextcord.errors import Forbidden, HTTPException

from utilities import (
    wait_for_event, act_on_word_found, started_spying, 
    papocchio_url, stop_spying_string
)

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


censor_data: dict[
    int, dict[
        str | int, dict[
            str, str | bool | int
        ] | dict[
            str, dict[
                str, str | bool | int
            ]
        ]
    ]
] = {}


@Emilia.event
async def on_ready() -> None:
    print(f"...loading censor information from guilds directory...")
    global censor_data
    root, *_ = os.walk("guilds")
    for dir in root[1]:
        try:
            temp_censor = json.load(open(f"guilds/{dir}/censor.json"))
        except FileNotFoundError:
            temp_censor = {}
        try:
            temp_rules = json.load(open(f"guilds/{dir}/rules.json"))
        except FileNotFoundError:
            temp_rules = {}
        censor_data[int(dir)] = temp_censor | temp_rules
    print(f"...({Emilia.user.name}#{Emilia.user.discriminator}) online")


@Emilia.event
async def on_message(message: Message) -> None:
    if isinstance(message, NoneType):
        return
    author = message.author
    if (author == Emilia.user):
        return
    for word, instructions in censor_data[message.guild.id].items():
        if (isinstance(word, int)): # Must be a censor_data[guild.id][user.id]
            if (word != author.id):
                continue
            for word_, instructions_ in censor_data[message.guild.id][author.id].items():
                if word_.lower() in message.content.lower():
                    await act_on_word_found(word_, instructions_, message, author)
                    break
            break
        if word.lower() in message.content.lower():
            await act_on_word_found(word, instructions, message, author)
            break
    else:
        await Emilia.process_commands(message)


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


@Emilia.slash_command(description="Add a word to the soviet censor list")
@has_permissions(administrator=True)
async def censor(
        interaction: Interaction, 
        word: str, reason: str, embed: bool,
        action: int = SlashOption(
            name="action", description="Action to take on word match",
            choices={"just Delete": 0, "also Kick": 1, "also Ban": 2},
        )
    ):
    path = f"guilds/{interaction.guild.id}/censor.json"
    if (not os.path.isfile(path)):
        try:
            file = open(path, "w")
        except FileNotFoundError:
            os.mkdir(f"guilds/{interaction.guild.id}")
            file = open(path, "w")
        file.write(r"{}")
        file.close()
    with open(path, "r") as file:
        censor: dict = json.load(file)
        censor[word] = {"reason": reason, "embed": embed, "action": action}
        try:
            censor_data[interaction.guild.id]
        except KeyError:
            censor_data[interaction.guild.id] = {}
        censor_data[interaction.guild.id][word.lower()] = {"reason": reason, "embed": embed, "action": action}
    with open(path, "w") as file:
        json.dump(censor, file, indent=4)
    await interaction.channel.send(embed=Embed(title="Censor", description=f"Added ||{word}|| to censor list", color=Color.red()))
    await interaction.response.send_message(f"Word ||{word}|| added to soviet censor list", ephemeral=True)


@Emilia.slash_command(description="Remove a word from the soviet censor list")
@has_permissions(administrator=True)
async def uncensor(interaction: Interaction, word: str) -> None:
    path = f"guilds/{interaction.guild.id}/censor.json"
    global censor_data
    try:
        censor_data[interaction.guild.id].pop(word.lower())
    except KeyError:
        await interaction.response.send_message(f"Word ||{word}|| not found in censor list", ephemeral=True)
    else:
        with open(path, "w") as file:
            json.dump(censor_data[interaction.guild.id], file, indent=4)
        await interaction.channel.send(embed=Embed(title="Censor", description=f"Removed ||{word}|| from censor list", color=Color.red()))
        await interaction.response.send_message(f"Word ||{word}|| removed from soviet censor list", ephemeral=True)


@Emilia.slash_command(description="Set a censor rule for a certain user")
async def user_censor(
        interaction: Interaction, user: User, 
        word: str, reason: str, embed: bool,
        action: int = SlashOption(
            name="action", description="Action to take on word match",
            choices={"just Delete": 0, "also Kick": 1, "also Ban": 2},
        )
    ):
    path = f"guilds/{interaction.guild.id}/rules.json"
    if (not os.path.isfile(path)):
        try:
            file = open(path, "w")
        except FileNotFoundError:
            os.mkdir(f"guilds/{interaction.guild.id}")
            file = open(path, "w")
        file.write(r"{}")
        file.close()
    with open(path, "r") as file:
        try:
            censor_data[interaction.guild.id]
        except KeyError:
            censor_data[interaction.guild.id] = {}
        try:
            censor_data[interaction.guild.id][user.id]
        except KeyError:
            censor_data[interaction.guild.id][user.id] = {}
        censor_data[interaction.guild.id][user.id][word.lower()] = {"reason": reason, "embed": embed, "action": action}
    with open(path, "w") as file:
        temp_ = {key: value for key, value in censor_data[interaction.guild.id].items() if isinstance(key, int)}
        json.dump(temp_, file, indent=4)
    await interaction.channel.send(embed=Embed(title="Censor", description=f"Added ||{word}|| to censor list for {user.mention}", color=Color.red()))
    await interaction.response.send_message(f"Word ||{word}|| added to soviet censor list for {user.mention}", ephemeral=True)


@Emilia.slash_command(description="Remove a censor rule for a certain user")
async def user_uncensor(interaction: Interaction, user: User, word: str) -> None:
    path = f"guilds/{interaction.guild.id}/rules.json"
    global censor_data
    try:
        censor_data[interaction.guild.id][user.id].pop(word.lower())
    except KeyError:
        await interaction.response.send_message(f"Word ||{word}|| not found in censor list for {user.mention}", ephemeral=True)
    else:
        with open(path, "w") as file:
            temp_ = {key: value for key, value in censor_data[interaction.guild.id].items() if isinstance(key, int)}
            json.dump(temp_, file, indent=4)
        await interaction.channel.send(embed=Embed(title="Censor", description=f"Removed ||{word}|| from censor list for {user.mention}", color=Color.red()))
        await interaction.response.send_message(f"Word ||{word}|| removed from soviet censor list for {user.mention}", ephemeral=True)


@Emilia.slash_command(description="List all censor rules")
async def see_censors(interaction: Interaction) -> None:
    try:
        censor = censor_data[interaction.guild.id]
    except KeyError:
        await interaction.response.send_message("No censor rules found", ephemeral=True)
        return
    embed = Embed(title="Censor", description="All censor rules", color=Color.red())
    for key, value in censor.items():
        try:
            int(key) # If key is an int, it's a user
        except ValueError:
            embed.add_field(name=key, value=f"Reason: {value['reason']}\nAction: {value['action']}\nEmbed: {value['embed']}", inline=False)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Censor list sent", ephemeral=True)


@Emilia.slash_command(description="List all censor rules for a certain user")
async def see_user_censors(interaction: Interaction, user: User) -> None:
    try:
        censor = censor_data[interaction.guild.id][str(user.id)]
    except KeyError:
        await interaction.response.send_message(f"No censor rules found for {user.mention}", ephemeral=True)
        return
    embed = Embed(title="Censor", description=f"All censor rules for {user.mention}", color=Color.red())
    for key, value in censor.items():
        embed.add_field(name=key, value=f"Reason: {value['reason']}\nAction: {value['action']}\nEmbed: {value['embed']}", inline=False)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message(f"Censor list for {user.mention} sent", ephemeral=True)


Emilia.run(open("token.txt").read())