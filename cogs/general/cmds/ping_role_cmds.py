from discord.ext import commands
import discord, datetime, math, importlib

import bot_utils.universals as univ

class PingRoleCMDs(commands.Cog, name="Pingable Roles"):
    def __init__(self, bot):
        self.bot = bot
        importlib.reload(univ)

    @commands.command(aliases = ["pingrole", "roleping", "role_ping"])
    async def ping_role(self, ctx, *, role_name):
        """Pings the role specified if the role isn't on cooldown and has been added to a list."""

        ping_roles = self.bot.config[ctx.guild.id]["pingable_roles"]

        if ping_roles == {}:
            await ctx.send("There are no roles for you to ping!")
            return

        role_obj = None

        for role in ctx.guild.roles:
            if role.name.lower() == role_name.lower():
                role_obj = role

        if role_obj == None:
            await ctx.send("That role doesn't exist!")
            return
        if not str(role_obj.id) in ping_roles.keys():
            await ctx.send("That role isn't pingable!")
            return

        role_entry = ping_roles[str(role_obj.id)]

        now = datetime.datetime.utcnow()
        time_period = datetime.timedelta(seconds=role_entry["time_period"])
        last_used = datetime.datetime.utcfromtimestamp(role_entry["last_used"])
        next_use = last_used + time_period

        if now < next_use:
            till_next_time = next_use - now
            till_next = till_next_time.total_seconds()

            hours = math.floor(till_next / 3600)
            till_next %= 3600
            minutes = math.floor(till_next / 60)
            till_next %= 60
            seconds = math.floor(till_next)

            time_group = []
            hours_string = f"{hours} hours" if hours != 1 else f"{hours} hour"
            if hours != 0:
                time_group.append(hours_string)
            minutes_string = f"{minutes} minutes" if minutes != 1 else f"{minutes} minutes"
            if minutes != 0:
                time_group.append(minutes_string)
            seconds_string = f"{seconds} seconds" if seconds != 1 else f"{seconds} seconds"
            if seconds != 0:
                time_group.append(seconds_string)

            time_text = ", ".join(time_group)
            await ctx.send(f"You cannot ping that role yet! Please wait: `{time_text}` before trying to ping the role again.")
            return
        else:
            await role_obj.edit(mentionable=True)
            await ctx.send(role_obj.mention)
            await role_obj.edit(mentionable=False)

            self.bot.config[ctx.guild.id]["pingable_roles"][str(role_obj.id)]["last_used"] = now.timestamp()

    @commands.group()
    @commands.check(univ.proper_permissions)
    async def manage_ping_roles(self, ctx):
        """The base command for managing all of the pingable roles. See the help for the subcommands for more info.
        Only people with Manage Server permissions or higher can use this."""
        
        if ctx.invoked_subcommand == None:
            list_cmd = self.bot.get_command("manage_ping_roles list")
            await ctx.invoke(list_cmd)

    @manage_ping_roles.command(name = "list")
    @commands.check(univ.proper_permissions)
    async def _list(self, ctx):
        """Returns a list of roles that have been made pingable, and their cooldown in seconds."""

        ping_roles = self.bot.config[ctx.guild.id]["pingable_roles"]

        if ping_roles == {}:
            await ctx.send("There are no roles added!")
            return

        role_list = []
        
        for role in ping_roles.keys():
            role_obj = ctx.guild.get_role(int(role))
            if role_obj != None:
                role_list.append(f"`{role_obj.name}, {role['time_period']} second cooldown`")
            else:
                del self.bot.config[ctx.guild.id]["pingable_roles"][role]

        if role_list != []:
            role_str = ", ".join(role_list)
            await ctx.send(f"Pingable roles: {role_str}")
        else:
            await ctx.send("There are no roles added!")

    @manage_ping_roles.command()
    @commands.check(univ.proper_permissions)
    async def add(self, ctx, role_name, cooldown):
        """Adds the role to the roles able to be pinged. 
        The role name is case-sensitive, and must be in quotes if it’s over one word. 
        The cooldown can be in seconds, minutes, or hours (ex. 1s, 1m, 1h)."""

        role_obj = discord.utils.get(ctx.guild.roles, name = role_name)
        if role_obj == None:
            await ctx.send("That's not a role! Make sure it's spelled correctly, and if it has multiple words, that it's in quotes.")
            return

        if str(role_obj.id) in self.bot.config[ctx.guild.id]["pingable_roles"]:
            await ctx.send("That role is already pingable! If you wish to change the cooldown, for now, remove and re-add the role.")
            return

        last_char = cooldown[-1]
        num_cooldown = cooldown[:-1]

        if not num_cooldown.isdigit():
            await ctx.send("Invalid cooldown! Make sure you have a time period, and the number's positive.")
            return

        multiplicity = 0

        if last_char.lower() == "h":
            multiplicity = 3600
        if last_char.lower() == "m":
            multiplicity = 60
        if last_char.lower() == "s":
            multiplicity = 1

        if multiplicity == 0:
            await ctx.send("Invalid cooldown! Make sure you have a time period, and the number's positive.")
            return

        period = int(num_cooldown) * multiplicity

        self.bot.config[ctx.guild.id]["pingable_roles"][str(role_obj.id)] = {
            "time_period": period,
            "last_used": 0
        }

        await ctx.send("Role added!")

    @manage_ping_roles.command()
    @commands.check(univ.proper_permissions)
    async def remove(self, ctx, *, role_name):
        """removes that role from the roles able to be pinged. 
        Role name is case-sensitive, although it does not need to be in quotes if it’s over one word. 
        This is the only way to ‘edit’ a role’s cooldown; removing it and adding it back in with the new cooldown."""

        ping_roles = self.bot.config[ctx.guild.id]["pingable_roles"]

        if ping_roles == {}:
            await ctx.send("There are no roles added for you to remove!")
            return

        role_obj = discord.utils.get(ctx.guild.roles, name = role_name)

        if role_obj == None:
            await ctx.send("That role doesn't exist!")
            return
        if not str(role_obj.id) in ping_roles.keys():
            await ctx.send("That role isn't on the ping list!")
            return

        del self.bot.config[ctx.guild.id]["pingable_roles"][str(role_obj.id)]

        await ctx.send("Deleted!")

def setup(bot):
    bot.add_cog(PingRoleCMDs(bot))
