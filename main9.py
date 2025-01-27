import discord
from discord.ext import commands
import random
import asyncio

BOT_TOKEN = "MTI2MDQzODc1MDExOTU5MjAxOA.Gt6gJ2.K9104dwxFH-z10-E0p3hE9cgVNGEt6hFw6ixrU"
CHANNEL_ID = 1260445599443062824
PUBLIC_KEY = "2228e8f50ff38c8fe501700947d87e57f6a9f44194877b7c0029574c45773ac1"
APPLICATION_ID = 1260438750119592018

# Queue Numbers
queues = {
    "MWIII": [],
    "MWII": [],
    "VG": [],
    "CW": [],
    "WWII": [],
    "IW": [],
    "BO3": [],
    "AW": [],
    "BO2": [],
    "BO1": [],
}

# Hardpoint Map Options
hardpoints = {
    "MWIII": ["6 Star", "Karachi", "Rio", "Sub Base", "Vista", "Skidrow", "Invasion"],
    "MWII": ["Embassy", "Fortress", "Hotel", "Mercado", "Hydroelectric"],
    "VG": ["Tuscan", "Bocage", "Berlin", "Gavutu", "Gavutu"],
    "CW": ["Checkmate", "Apocalypse", "Garrison", "Moscow", "Raid"],

}

# SND Map Options
snds = {
    "MWIII": ["Terminal", "Skidrow", "Rio", "Karachi", "Highrise", "Invasion"],
    "MWII": ["El Asilo", "Fortress", "Hotel", "Embassy", "Mercado"],
    "VG": ["Tuscan", "Bocage", "Berlin", "Desert Siege"],
    "CW": ["Express", "Miami", "Moscow", "Raid", "Standoff"],
}

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

class QueueView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.create_buttons()

    def create_buttons(self):
        for game in queues.keys():
            join_button = self.create_join_button(game)
            self.add_item(join_button)
        leave_button = self.create_leave_button()
        self.add_item(leave_button)

    def create_join_button(self, game):
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
            
            if len(queue) == 2: #supposed to be 8 people, changing to 2 for testing
                await self.create_teams(interaction.channel, queue, game)

        button.callback = join_queue
        return button

    def create_leave_button(self):
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
        hardpoint = random.choice(hardpoints[game])
        hardpoint2 = random.choice(hardpoints[game])
        if hardpoint == hardpoint2:
            while hardpoint == hardpoint2:
                hardpoint2 = random.choice(hardpoints[game])
        snd = random.choice(snds[game])
        return f" Mapset\n Hardpoint: {hardpoint}\n Hardpoint: {hardpoint2} \n Search and Destroy: {snd}"

    async def create_teams(self, channel, queue, game):
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

        # Create mapset string and send it to match text channel
        message = self.create_mapset(game)
        await match_channel.send(f"Welcome to your {game} match! \n \n {message}")

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
        member_names = [member.name for member in team1 + team2]
        await match_channel.send(f"\n Members in this match: {', '.join(member_names)}")
        countdown_message = await match_channel.send("Channels will be deleted if a user does not join in the next 5 minutes")

        # Schedule deletion of the category after 5 minutes to check if all members have joined
        await self.schedule_initial_check(category, 1 * 60, team1 + team2, countdown_message) # changed to 1 minute for testing

    async def schedule_initial_check(self, category, delay, members, countdown_message):
        for i in range(delay, 0, -1):
            await countdown_message.edit(content=f"\n Channels will be deleted if a user does not join in the next {i} seconds")
            await asyncio.sleep(1)

        if all(any(member in vc.members for vc in category.voice_channels) for member in members):
            # Schedule deletion of the category after 50 minutes or when all members have left
            await self.schedule_category_deletion(category, 50 * 60)
        else:
            await self.delete_category_and_channels(category)

    async def schedule_category_deletion(self, category, delay):
        await asyncio.sleep(delay)
        if all(len(vc.members) == 0 for vc in category.voice_channels):
            await self.delete_category_and_channels(category)
        else:
            await self.schedule_category_deletion(category, 5 * 60)  # Check again in 5 minutes

    async def delete_category_and_channels(self, category):
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
            embed.add_field(name=f"{game} Queue: ", value=len(queue))
        await embed_message.edit(embed=embed)
        await asyncio.sleep(1)

bot.run(BOT_TOKEN)