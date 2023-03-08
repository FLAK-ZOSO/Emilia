from typing import Iterable
from nextcord.ext.commands import Bot
from nextcord import Member, User
from nextcord.message import Message
from nextcord.embeds import Embed
from nextcord.colour import Color


async def wait_for_event(bot: Bot, event, **options):
    args = await bot.wait_for(event, **options)
    if not isinstance(args, Iterable):
        args = [args]
    return event, *args

async def act_on_word_found(
        word: str, instructions: dict[str, str | int | bool], 
        message: Message, author: Member
    ):
    print(f"{instructions=}")
    if ("reason" in instructions.keys()):
        reason_ = instructions["reason"]
    else:
        try:
            reason_ = instructions[word]["reason"]
        except KeyError:
            reason_ = "{...}"
    reason = f"""
        Word: ||{word}||
        Reason: {reason_}
    """
    embed_ = Embed(
        title="Censored", description=reason,
        color=Color.red(), url="https://github.com/FLAK-ZOSO/Emilia"
    )
    if ("action" in instructions.keys()):
        action = instructions["action"]
    else:
        try:
            action = instructions[word]["action"]
        except KeyError:
            action = 0
    if ("embed" in instructions.keys()):
        embed = instructions["embed"]
    else:
        try:
            embed = instructions[word]["embed"]
        except KeyError:
            embed = True
    match action:
        case 0:
            if (embed):
                await message.reply(embed=embed_)
            await message.delete()
        case 1:
            if (embed):
                await message.reply(embed=embed_)
                await author.send(embed=embed_)
            await message.delete()
            await author.kick(reason=reason)
        case 2:
            if (embed):
                await message.reply(embed=embed_)
                await author.send(embed=embed_)
            await message.delete()
            await author.ban(reason=reason)


def started_spying(user: Member | User) -> Embed:
    return Embed(
        title = "SPY", 
        description = f"I started spying on {user.mention}.", 
        color = Color.red()
    )


papocchio_url = "https://static.miraheze.org/nonciclopediawiki/c/cd/Papocchio_2000x2000.png"
stop_spying_string = "Stop spying on "