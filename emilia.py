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


censor_data: dict[int, dict[str, dict[str, str | bool | int]]] = {}


@Emilia.event
async def on_ready() -> None:
    print(f"...loading censor information from guilds directory...")
    global censor_data
    root, *_ = os.walk("guilds")
    for dir in root[1]:
        censor_data[int(dir)] = json.load(open(f"guilds/{dir}/censor.json"))
    print(f"...({Emilia.user.name}#{Emilia.user.discriminator}) online")


@Emilia.event
async def on_message(message: Message) -> None:
    author = message.author
    for word, instructions in censor_data[message.guild.id].items():
        if word.lower() in message.content.lower():
            reason = f"""
                Word: ||{word}||
                Reason: {instructions['reason']}
            """
            embed_ = Embed(
                title="Censored", description=reason,
                color=Color.red(), url="https://github.com/FLAK-ZOSO/Emilia"
            )
            match instructions["action"]:
                case 0:
                    if (instructions["embed"]):
                        await message.reply(embed=embed_)
                    await message.delete()
                case 1:
                    if (instructions["embed"]):
                        await message.reply(embed=embed_)
                        await author.send(embed=embed_)
                    await message.delete()
                    await author.kick(reason=reason)
                case 2:
                    if (instructions["embed"]):
                        await message.reply(embed=embed_)
                        await author.send(embed=embed_)
                    await message.delete()
                    await author.ban(reason=reason)
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
        censor_data[interaction.guild.id][word] = {"reason": reason, "embed": embed, "action": action}
    with open(path, "w") as file:
        json.dump(censor, file, indent=4)
    await interaction.channel.send(embed=Embed(title="Censor", description=f"Added {word} to censor list", color=Color.red()))
    await interaction.response.send_message(f"Word {word} added to soviet censor list", ephemeral=True)


@Emilia.slash_command(description="Remove a word from the soviet censor list")
@has_permissions(administrator=True)
async def uncensor(interaction: Interaction, word: str) -> None:
    path = f"guilds/{interaction.guild.id}/censor.json"
    global censor_data
    try:
        censor_data[interaction.guild.id].pop(word)
    except KeyError:
        await interaction.response.send_message(f"Word {word} not found in censor list", ephemeral=True)
    else:
        with open(path, "w") as file:
            json.dump(censor_data[interaction.guild.id], file, indent=4)
        await interaction.channel.send(embed=Embed(title="Censor", description=f"Removed {word} from censor list", color=Color.red()))
        await interaction.response.send_message(f"Word {word} removed from soviet censor list", ephemeral=True)


Emilia.run(open("token.txt").read())