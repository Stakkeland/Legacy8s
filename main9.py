import discord
from discord.ext import commands
import random
import asyncio

BOT_TOKEN = "MTMzMzY1MTgwNjE0ODEwMDEwNg.GRWneG.PZqfo9jyS8OxitYGYHqmsHwylLejaCFzu3exY0"
CHANNEL_ID = 1333649194639949825
PUBLIC_KEY = "5e5e8cc217c23f92ae66d7c26e9797f05d6c33150f3cc82c37d19e465945e8dc"
APPLICATION_ID = 1333651806148100106

# Queue Numbers
queues = {
    "MWIII": [],
    "MWII": [],
    "Vanguard": [],
    "Cold War": [],
    "World War II": [],
    "Infinite Warfare": [],
    "BO3": [],
    "AW": [],
    "BO2": [],
}

# Hardpoint Map Options
hardpoints = {
    "MWIII": ["6 Star", "Karachi", "Rio", "Sub Base", "Vista", "Skidrow", "Invasion"],
    "MWII": ["Embassy", "Fortress", "Hotel", "Mercado", "Hydroelectric"],
    "Vanguard": ["Tuscan", "Bocage", "Berlin", "Gavutu", "Gavutu"],
    "Cold War": ["Checkmate", "Apocalypse", "Garrison", "Moscow", "Raid"],
    "World War II": ["Ardennes Forest","Saint Marie Du Mont", "London Docks", "Valkyrie", "Gibraltar"],
    "Infinite Warfare": ["Throwback", "Scorch", "Mayday", "Precinct", "Breakout", "Frost"],
    "BO3": ["Evac", "Fringe", "Stronghold", "Hunted", "Breach", "Redwood"], # Not right, AI
    "AW": ["Detroit", "Bio Lab", "Solar", "Recovery", "Retreat", "Ascend"], # Not right, AI
    "BO2": ["Slums", "Raid", "Standoff", "Plaza", "Meltdown", "Express"], # Not right, AI

}

# SND Map Options
snds = {
    "MWIII": ["Terminal", "Skidrow", "Rio", "Karachi", "Highrise", "Invasion"],
    "MWII": ["El Asilo", "Fortress", "Hotel", "Embassy", "Mercado"],
    "Vanguard": ["Tuscan", "Bocage", "Berlin", "Desert Siege"],
    "Cold War": ["Express", "Miami", "Moscow", "Raid", "Standoff"],
    "World War II": ["Ardennes Forest", "Saint Marie Du Mont", "London Docks", "Valkyrie", "USS Texas"],
    "Infinite Warfare": ["Crusher", "Retaliation", "Scorch", "Frost", "Throwback", "Mayday"],
    "BO3": ["Fringe", "Stronghold", "Hunted", "Evac", "Breach", "Redwood"], # Not right, AI
    "AW": ["Detroit", "Bio Lab", "Solar", "Recovery", "Retreat", "Ascend"], # Not right, AI
    "BO2": ["Slums", "Raid", "Standoff", "Plaza", "Meltdown", "Express"], # Not right, AI
}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

class QueueView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.create_buttons()

    def create_buttons(self):
        '''Create a join button for each game in the queue'''
        for game in queues.keys():
            join_button = self.create_join_button(game)
            self.add_item(join_button)
        leave_button = self.create_leave_button()
        self.add_item(leave_button)

    def create_join_button(self, game):
        '''Create a button to join the queue for a game'''
        button = discord.ui.Button(label=game, style=discord.ButtonStyle.success)

        async def join_queue(interaction: discord.Interaction):
            user = interaction.user
            # Check if user is already in any queue
            for other_game, queue in queues.items():
                if user in queue:
                    await interaction.response.send_message(f"{user.name}, you are already in the {other_game} queue!", ephemeral=True)
                    return

            queue = queues[game]
            queue.append(user)
            await interaction.response.send_message(f"{user.name} has joined the {game} queue!", ephemeral=True)
            
            if len(queue) == 2: #supposed to be 8 people, changing to 1 for testing
                await self.create_teams(interaction.channel, queue, game)

        button.callback = join_queue
        return button

    def create_leave_button(self):
        '''Create a button to leave the queue'''
        button = discord.ui.Button(label="Leave Queue", style=discord.ButtonStyle.danger)

        async def leave_queue(interaction: discord.Interaction):
            user = interaction.user
            for game, queue in queues.items():
                if user in queue:
                    queue.remove(user)
                    await interaction.response.send_message(f"{user.name} has left the {game} queue.", ephemeral=True)
                    return
            await interaction.response.send_message(f"{user.name}, you are not in any queue.", ephemeral=True)

        button.callback = leave_queue
        return button
    
    def create_mapset(self, game):
        '''Create a random mapset for the given game'''
        hardpoint = random.choice(hardpoints[game])
        hardpoint2 = random.choice(hardpoints[game])
        if hardpoint == hardpoint2:
            while hardpoint == hardpoint2:
                hardpoint2 = random.choice(hardpoints[game])
        snd = random.choice(snds[game])

        # Send the mapset in an embed
        embed = discord.Embed(
        title=f"Mapset",
        )
        embed.set_footer(text="Legacy 8's")
        embed.add_field(name="Hardpoint:", value=hardpoint, inline=True)
        embed.add_field(name="Hardpoint:", value=hardpoint2, inline=True)
        embed.add_field(name="Search and Destroy:", value=snd, inline=True)
        return embed

    async def create_teams(self, channel, queue, game): # Need to split this function up into multiple functions
        '''Create two teams and send the mapset'''
        random.shuffle(queue)
        team1 = queue[:1]
        team2 = queue[1:]

        guild = channel.guild
        category = await guild.create_category(f"{game} Match")

        match_channel = await category.create_text_channel(f"{game} Match Chat")

        team1_channel = await category.create_voice_channel("Team 1")
        team2_channel = await category.create_voice_channel("Team 2")

        team1_invite = await team1_channel.create_invite(max_age=300)
        team2_invite = await team2_channel.create_invite(max_age=300)

        # Send the mapset in an embed
        mapset_embed = self.create_mapset(game)
        await match_channel.send(f"Welcome to your {game} match!")
        await match_channel.send(embed=mapset_embed)

        # Send Dm to team members with invite link
        for member in team1:
            try:
                await member.send(f"You have been assigned to Team 1 for {game}. Join the voice channel using this link: {team1_invite}")
            except discord.Forbidden:
                await channel.send(f"Could not send invite to {member.name}.", ephemeral=True)
        
        for member in team2:
            try:
                await member.send(f"You have been assigned to Team 2 for {game}. Join the voice channel using this link: {team2_invite}")
            except discord.Forbidden:
                await channel.send(f"Could not send invite to {member.name}.", ephemeral=True)

        queue.clear()

        # Send the names of all Discord users in the category and the countdown message
        member_mentions = [member.mention for member in team1 + team2]
        await match_channel.send(f"Members in this match: {' , '.join(member_mentions)}")
        countdown_message = await match_channel.send("Channels and Match will end if all users do not join in the next 4 minutes")

        # Schedule deletion of the category after 4 minutes to check if all members have joined
        await self.schedule_initial_check(category, 4, team1 + team2, countdown_message)

    async def schedule_initial_check(self, category, delay_mins, members, countdown_message):
        '''Schedule a countdown message to be edited every second for a delay'''
        for i in range(delay_mins, 0, -1):
            await countdown_message.edit(content=f"Channels and Match will end if all users do not join in the next {i} minutes")
            await asyncio.sleep(60)

        for i in range(60, 0, -1):
            await countdown_message.edit(content=f"Channels and Match will end if all users do not join in the next {i} seconds")
            await asyncio.sleep(1)

        if all(any(member in vc.members for vc in category.voice_channels) for member in members):
            # Schedule deletion of the category after 40 minutes or when all members have left
            await countdown_message.delete()
            await self.schedule_category_deletion(category, 40 * 60)
        else:
            await countdown_message.delete()
            await self.delete_category_and_channels(category)

    async def schedule_category_deletion(self, category, delay):
        '''Schedule deletion of the category after a delay if all voice channels are empty'''
        await asyncio.sleep(delay)
        if all(len(vc.members) == 0 for vc in category.voice_channels):
            await self.delete_category_and_channels(category)
        else:
            await self.schedule_category_deletion(category, 5 * 60)  # Check again in 5 minutes

    async def delete_category_and_channels(self, category):
        '''Delete the category and all its channels'''
        for channel in category.channels:
            await channel.delete()
        await category.delete()

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)

    embed = discord.Embed(
        description="Join the queue by clicking a button below.",
        title="Queue Manager"
    )
    embed.set_footer(text="CDL Legacy 8's")

    view = QueueView()
    embed_message = await channel.send(embed=embed, view=view)

    while True:
        embed.clear_fields()
        for game, queue in queues.items():
            embed.add_field(name=f"{game} : ", value=len(queue))
        await embed_message.edit(embed=embed)
        await asyncio.sleep(1)

bot.run(BOT_TOKEN)