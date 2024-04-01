#!/usr/bin/env python3
import json
import os
from asyncio import create_task, Task, wait, FIRST_COMPLETED
from datetime import datetime
from types import NoneType
import random

import nextcord
from nextcord.ext.commands import Bot, Context, command, has_permissions
from nextcord import SlashOption, User, Member
from nextcord.abc import GuildChannel, Messageable
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
    if (stop_spying_string in message.content):
        return
    for word, instructions in censor_data[message.guild.id].items():
        if (isinstance(word, int) or word.isdigit()): # Must be a censor_data[guild.id][str(user.id)]
            if (word != str(author.id)):
                continue
            for word_, instructions_ in censor_data[message.guild.id][str(author.id)].items():
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


@Emilia.slash_command(name="delete", description="Delete some of the last N messages in the channel based on content")
@has_permissions(administrator=True)
async def delete(
        interaction: Interaction,
        number: int = SlashOption(
            name="number",
            description="The number of messages from which delete those ones which match the condition",
            required=True,
        ),
        content: str = SlashOption(
            name="content",
            description="The content to match",
            required=True,
        )) -> None:
    counter = 0
    def _check(message: Message) -> bool:
        nonlocal counter
        if (content in message.content):
            counter += 1
            return True
        return False
    await interaction.channel.purge(limit=number + 1, check=_check)
    await interaction.response.send_message(f"Deleted {counter} messages containing *{content}* from a group of {number}", ephemeral=True)


@Emilia.slash_command(description="Add a word to the soviet censor list")
@has_permissions(administrator=True)
async def censor(
        interaction: Interaction, 
        word: str, reason: str, embed: bool,
        action: int = SlashOption(
            name="action", description="Action to take on word match",
            choices={"just Delete": 0, "also Kick [must be admin]": 1, "also Ban [must be admin]": 2},
        )
    ):
    action = action if interaction.user.guild_permissions.administrator else 0
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
            choices={"just Delete": 0, "also Kick [must be admin]": 1, "also Ban [must be admin]": 2},
        )
    ):
    action = action if interaction.user.guild_permissions.administrator else 0
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
        print(f"{censor_data[interaction.guild.id]=}")
        try:
            censor_data[interaction.guild.id][str(user.id)]
        except KeyError:
            censor_data[interaction.guild.id][str(user.id)] = {}
        print(f"{censor_data[interaction.guild.id][str(user.id)]=}")
        censor_data[interaction.guild.id][str(user.id)][word.lower()] = {"reason": reason, "embed": embed, "action": action}
        print(f"{censor_data[interaction.guild.id][str(user.id)][word.lower()]=}")
    with open(path, "w") as file:
        temp_ = {key: value for key, value in censor_data[interaction.guild.id].items() if key.isdigit()}
        print("THEN...")
        print(f"{temp_=}")
        print(f"{censor_data[interaction.guild.id]=}")
        print(f"{censor_data[interaction.guild.id][str(user.id)]=}")
        print(f"{censor_data[interaction.guild.id][str(user.id)][word.lower()]=}")
        json.dump(temp_, file, indent=4)
    await interaction.channel.send(embed=Embed(title="Censor", description=f"Added ||{word}|| to censor list for {user.mention}", color=Color.red()))
    await interaction.response.send_message(f"Word ||{word}|| added to soviet censor list for {user.mention}", ephemeral=True)


@Emilia.slash_command(description="Remove a censor rule for a certain user")
async def user_uncensor(interaction: Interaction, user: User, word: str) -> None:
    path = f"guilds/{interaction.guild.id}/rules.json"
    global censor_data
    try:
        censor_data[interaction.guild.id][str(user.id)].pop(word.lower())
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


@Emilia.slash_command(description="Spy a certain user. [NOTE: This command will die on bot shutdown]")
async def spy(interaction: Interaction, user: Member) -> None:
    author = interaction.user
    if (user.id == Emilia.user.id):
        await author.send(embed = Embed(
            title="You must be an idiot...",
            description="...I can't spy on myself!",
            color=Color.dark_theme()
        ))
        await interaction.response.send_message(
            embed=Embed(
                title="For everyone's information...",
                description=f"{author.mention} asked me to spy on myself! What an idiot!",
                color=Color.dark_theme()
            ), ephemeral=False
        )
        return
    await author.send(embed = started_spying(user))
    await interaction.response.send_message(f"Stop spying on {user.mention} by writing 'Stop spying on {user.name}'", ephemeral=True)

    while True:
        tasks = [
            create_task(wait_for_event(Emilia, "presence_update")),
            create_task(wait_for_event(Emilia, "user_update")),
            create_task(wait_for_event(Emilia, "message")),
            create_task(wait_for_event(Emilia, "typing"))
        ]

        pending: list[Task]
        done, pending = await wait(tasks, return_when=FIRST_COMPLETED)
        for task in pending:
            task.cancel()

        event, *args = list(done)[0].result()

        if event == "user_update":
            before: User
            after: User
            before, after = args
            if before.id == user.id:
                e = Embed(title = f"{after.name}#{after.discriminator}", color = Color.default())
                e.add_field(name = "Before", value = f"Avatar: {before.avatar}\n Username: {before.name}\n Discriminator: {before.discriminator}")
                e.add_field(name = "After", value = f"Avatar: {after.avatar}\n Username: {after.name}\n Discriminator: {after.discriminator}")
                e.set_footer(text = f"Time: {datetime.now()}")
                e.set_author(name = "Papocchio", icon_url = papocchio_url)
                e.set_thumbnail(url = after.avatar.url)
                await author.send(embed = e)
        
        elif event == "presence_update":
            before: Member
            after: Member
            before, after = args
            if before.id == user.id:
                e = Embed(title = f"{after.name}#{after.discriminator}", color = Color.default())
                try:
                    before_activity = before.activity.name
                    before_details = before.activity.details
                except AttributeError:
                    before_activity = before_details = "None"
                try:
                    after_activity = after.activity.name
                    after_details = after.activity.details
                except AttributeError:
                    after_activity = after_details = "None"
                e.add_field(name = "Before", value = f"Status: {before.status}\n Activity: {before_activity}\n Details: {before_details}\n Nickname: {before.nick}", inline = False)
                e.add_field(name = "After", value = f"Status: {after.status}\n Activity: {after_activity}\n Details: {after_details}\n Nickname: {after.nick}", inline = False)
                e.set_footer(text = f"Time: {datetime.now()}")
                e.set_author(name = "Papocchio", icon_url = papocchio_url)
                e.set_thumbnail(url = after.avatar.url)
                await author.send(embed = e)

        elif event == "typing":
            channel: Messageable | GuildChannel
            channel, user_typing, when_ = args
            if user == user_typing:
                e = Embed(title = f"{user.name}#{user.discriminator}", description = f"I caught {user.mention} typing in {channel.mention}.", color = Color.default())
                e.set_footer(text = f"Time: {datetime.now()}")
                e.set_author(name = "Papocchio", icon_url = papocchio_url)
                e.set_thumbnail(url = user.avatar.url)
                await author.send(embed = e)

        elif event == "message":
            message: Message = args[0]
            if message.author == user:
                e = Embed(title = f"{user.name}#{user.discriminator}", description = f"{user.mention} sent a message in {message.channel}.", color = Color.default())
                e.set_footer(text = f"Time: {datetime.now()}")
                e.set_author(name = "Papocchio", icon_url = papocchio_url)
                e.set_thumbnail(url = user.avatar.url)
                await author.send(embed = e)

            if message.author == author and stop_spying_string.lower() in message.content.lower():
                if (user.mention in message.content.lower()) or (user.name.lower() in message.content.lower()):
                    try:
                        await message.delete()
                    except Forbidden | MissingPermissions | HTTPException:
                        pass # It could have been already deleted by another thread
                    e = Embed(title = "STOP SPYING", description = f"Stopped spying {user.mention} ({user.name}#{user.discriminator}).")
                    e.set_footer(text = f"Time: {datetime.now()}")
                    e.set_author(name = "Papocchio", icon_url = papocchio_url)
                    e.set_thumbnail(url = user.avatar.url)
                    await author.send(embed = e)
                    return


@Emilia.slash_command(name="dump_nicknames", description="Dump all {member.id: nickname} pairs to .json and send it to the channel", guild_ids=[1033496612355461131, 790997924896833596])
async def dump_nicknames(interaction: Interaction) -> None:
    nicknames = {member.id: member.nick for member in interaction.guild.members}
    print(f"{nicknames=}")
    for key, value in nicknames.items():
        if value is None:
            nicknames[key] = interaction.guild.get_member(key).global_name
        if nicknames[key] is None:
            nicknames[key] = interaction.guild.get_member(key).name
    print(f"{nicknames=}")
    try:
        with open(f"guilds/{interaction.guild.id}/nicknames.json", "w") as file:
            json.dump(nicknames, file, indent=4)
    except FileNotFoundError:
        os.mkdir(f"guilds/{interaction.guild.id}")
        with open(f"guilds/{interaction.guild.id}/nicknames.json", "w") as file:
            json.dump(nicknames, file, indent=4)
    await interaction.channel.send(file=nextcord.File(f"guilds/{interaction.guild.id}/nicknames.json"))
    await interaction.response.send_message("Nicknames dumped", ephemeral=True)

shuffling_nicknames = False

@Emilia.slash_command(name="shuffle_nicknames", description="Shuffle all nicknames in the server", guild_ids=[1033496612355461131, 790997924896833596])
async def shuffle_nicknames(interaction: Interaction) -> None:
    if shuffling_nicknames:
        interaction.response.send_message("Already shuffling...", ephemeral=True)
        return

    shuffling_nicknames = True
    nicknames = {member.id: member.nick for member in interaction.guild.members}
    for key, value in nicknames.items():
        if value is None:
            nicknames[key] = interaction.guild.get_member(key).name
    print(f"{nicknames=}")
    nicknames_ = list(nicknames.values())
    print(f"{nicknames_=}")
    random.shuffle(nicknames_)
    nicknames = list(zip(nicknames.keys(), nicknames_))
    print(f"{nicknames=}")
    for key, value in nicknames:
        try:
            await interaction.guild.get_member(key).edit(nick=value)
            print(f"Shuffled nickname for {interaction.guild.get_member(key).name} to {value}")
        except BaseException as e:
            shuffling_nicknames = False
            print(f"{e=}")
            print(f"Error shuffling nickname for {interaction.guild.get_member(key).name}")
    await interaction.channel.send(embed=Embed(title="Nicknames", description="Nicknames shuffled", color=Color.red()))
    await interaction.response.send_message("Nicknames shuffled", ephemeral=True)
    shuffling_nicknames = False


@Emilia.slash_command(name="reset_nicknames", description="Reset all nicknames in the server", guild_ids=[1033496612355461131, 790997924896833596])
async def reset_nicknames(interaction: Interaction) -> None:
    if shuffling_nicknames:
        interaction.response.send_message("Wait until end of shuffle...", ephemeral=True)
        return
    # reset all nicknames from guilds/guild.id/nicknames.json
    try:
        with open(f"guilds/{interaction.guild.id}/nicknames.json", "r") as file:
            nicknames = json.load(file)
    except FileNotFoundError:
        await interaction.response.send_message("No nicknames found", ephemeral=True)
        return
    for member in interaction.guild.members:
        try:
            await member.edit(nick=nicknames.pop(str(member.id)))
            print(f"Reset nickname for {member.name}")
        except:
            print(f"Error resetting nickname for {member.name}")
    await interaction.response.send_message("Nicknames reset", ephemeral=True)


Emilia.run(open("token.txt").read())
