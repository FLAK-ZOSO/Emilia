from typing import Iterable
from nextcord.ext.commands import Bot
from nextcord import Member
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