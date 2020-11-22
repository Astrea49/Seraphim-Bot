#!/usr/bin/env python3.7
import discord, re
import collections

import common.star_utils as star_utils
import common.utils as utils
import common.image_utils as image_utils

def cant_display(embed: discord.Embed, attachments: list, index = 0):
    attach_strs = collections.deque()

    for x in range(len(attachments)):
        if x < index:
            continue

        attachment = attachments[x]
        if attachment.is_spoiler():
            attach_strs.append(f"||[{attachment.filename}]({attachment.url})||")
        else:
            attach_strs.append(f"[{attachment.filename}]({attachment.url})")

    if index == 0:
        embed.add_field(name="Attachments", value="\n".join(attach_strs), inline=False)
    else:
        embed.add_field(name="Other Attachments", value="\n".join(attach_strs), inline=False)

    return embed

async def base_generate(bot, mes: discord.Message, no_attachments = False):
    # generates core of star messages
    image_url = ""

    if mes.embeds and mes.author.id == bot.user.id and \
    mes.embeds[0].author.name != bot.user.name and mes.embeds[0].fields != discord.Embed.Empty and \
    mes.embeds[0].footer.text != discord.Embed.Empty and mes.embeds[0].footer.text.startswith("ID:"): # all of this... for pinboard support
        send_embed = mes.embeds[0].copy() # it's using the same internal gen, so why not just copy it

        for x in range(len(send_embed.fields)):
            if send_embed.fields[x].name == "Original":
                send_embed.remove_field(x)
                break

        # next pieces of code make the embed more how a normally generated embed would be like
        send_embed.color = discord.Colour(0xcfca76)
        send_embed.timestamp = mes.created_at
        send_embed.set_footer() # will set footer to default, aka none

    elif mes.embeds != [] and ((mes.author.id in (270904126974590976, 499383056822435840) 
    and mes.embeds[0].author.name != discord.Embed.Empty) or (mes.author.id == bot.user.id 
    and mes.embeds[0].author.name != bot.user.name)): # if message is sniped message that's supported
        snipe_embed = mes.embeds[0]

        entry = bot.starboard.get(mes.id)

        if entry:
            author = await utils.user_from_id(bot, mes.guild, entry.author_id)
        else:
            author_id = star_utils.get_author_id(mes, bot)
            author = await utils.user_from_id(bot, mes.guild, author_id)
            
        author_str = ""
        if author == None:
            author_str = mes.embeds[0].author.name
        else:
            author_str = f"{author.display_name} ({str(author)})"

        icon = snipe_embed.author.icon_url if author == None else str(author.avatar_url_as(format=None,static_format="png",size=128))
        content = snipe_embed.description

        send_embed = discord.Embed(title="Sniped:", colour=discord.Colour(0xcfca76), 
        description=content, timestamp=mes.created_at)
        send_embed.set_author(name=author_str, icon_url=icon)

    elif mes.embeds != [] and mes.embeds[0].description != discord.Embed.Empty and mes.embeds[0].type == "rich": # generic embed support
        author = f"{mes.author.display_name} ({str(mes.author)})"
        icon = str(mes.author.avatar_url_as(format=None,static_format="png", size=128))

        send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=mes.embeds[0].description, timestamp=mes.created_at)
        send_embed.set_author(name=author, icon_url=icon)
        
    else:
        content = utils.get_content(mes)
        author = f"{mes.author.display_name} ({str(mes.author)})"
        icon = str(mes.author.avatar_url_as(format=None,static_format="png", size=128))

        if content != "":
            send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=content, timestamp=mes.created_at)
        else:
            send_embed = discord.Embed(colour=discord.Colour(0xcfca76), description=discord.Embed.Empty, timestamp=mes.created_at)
        send_embed.set_author(name=author, icon_url=icon)

        if mes.type == discord.MessageType.default and mes.reference:
            # checks if message has inline reply

            ref_author = None
            ref_auth_str = ""
            ref_mes_url = ""

            if mes.reference.cached_message:
                # saves time fetching messages if possible
                ref_author = mes.reference.cached_message.author
                ref_mes_url = mes.reference.cached_message.jump_url
            elif mes.reference.message_id:
                # fetches message from info given by MessageReference
                # note the message id might not be provided, so we check if it is
                ref_chan = bot.get_channel(mes.reference.channel_id)
                if ref_chan:
                    try:
                        ref_mes = await ref_chan.fetch_message(mes.reference.message_id)
                        ref_author = ref_mes.author
                        ref_mes_url = ref_mes.jump_url
                    except discord.HTTPException:
                        pass

            if ref_author:
                ref_auth_str = ref_author.display_name
            else:
                ref_auth_str = "a message"

            if not ref_mes_url and mes.reference.message_id and mes.reference.guild_id:
                ref_mes_url = f"https://discord.com/channels/{mes.reference.guild_id}/{mes.reference.channel_id}/{mes.reference.message_id}"

            send_embed.title = f"{mes.author.display_name} replied to {ref_auth_str}:"
            if ref_mes_url:
                send_embed.url = ref_mes_url

        if mes.embeds != [] and mes.embeds[0].type == "image" and mes.embeds[0].thumbnail.url != discord.Embed.Empty:
            image_url = mes.embeds[0].thumbnail.url

            if not no_attachments and mes.attachments:
                send_embed = cant_display(send_embed, mes.attachments, 0)
        elif not no_attachments and mes.attachments != []:
            if mes.attachments[0].proxy_url.lower().endswith(bot.image_extensions) and not mes.attachments[0].is_spoiler():
                image_url = mes.attachments[0].proxy_url

                if len(mes.attachments) > 1:
                    send_embed = cant_display(send_embed, mes.attachments, 1)
            else:
                send_embed = cant_display(send_embed, mes.attachments, 0)
        else:
            urls = re.findall(r"((\w+:\/\/)[-a-zA-Z0-9:@;?&=\/%\+\.\*!'\(\),\$_\{\}\^~\[\]`#|]+)", content)
            if urls != []:
                first_url = urls[0][0]
                
                possible_url = await image_utils.get_image_url(first_url)
                if possible_url != None:
                    image_url = possible_url

            if not no_attachments and mes.attachments:
                send_embed = cant_display(send_embed, mes.attachments, 0)

    if image_url != "":
        send_embed.set_image(url=image_url)

    return send_embed

async def star_generate(bot, mes):
    # base generate but with more fields
    send_embed = await base_generate(bot, mes)
    send_embed.add_field(name="Original", value=f"[Jump]({mes.jump_url})", inline=True)
    send_embed.set_footer(text=f"ID: {mes.id}")

    return send_embed

async def send(bot, mes, unique_stars, forced = False):
    # sends message to starboard channel

    send_embed = await star_generate(bot, mes)
    starboard = mes.guild.get_channel(bot.config[mes.guild.id]["starboard_id"])

    if starboard:
        star_emoji = star_utils.get_star_emoji(unique_stars)
        if not forced:
            starred = await starboard.send(content=f"{star_emoji} **{unique_stars}** | {mes.channel.mention}", embed=send_embed)
        else:
            starred = await starboard.send(content=f"{star_emoji} **{unique_stars}** | {mes.channel.mention} (Forced Entry)", embed=send_embed)
        await starred.add_reaction("⭐")

        entry = bot.starboard.get(mes.id)
        entry.star_var_id = starred.id
        entry.starboard_id = starred.channel.id
        bot.starboard.update(entry)

        return starred

    return None