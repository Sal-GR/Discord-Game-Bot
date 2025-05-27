import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="info.env")
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

buzzer_locked = False
first_buzzer = None
BUZZER_SOUND = "buzzer.mp3"

class BuzzerView(discord.ui.View):
    @discord.ui.button(label="Buzz!", style=discord.ButtonStyle.red)
    async def buzz_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global buzzer_locked, first_buzzer

        if buzzer_locked:
            await interaction.response.send_message("❌ Someone already buzzed!", ephemeral=True)
            return

        buzzer_locked = True
        first_buzzer = interaction.user.display_name
        button.disabled = True
        await interaction.response.edit_message(view=self)

        # 🔊 Play the sound in user's voice channel
        if interaction.user.voice and interaction.user.voice.channel:
            vc_channel = interaction.user.voice.channel

            try:
                # Disconnect existing connections first (if any)
                if interaction.guild.voice_client:
                    await interaction.guild.voice_client.disconnect()

                vc = await vc_channel.connect()

                audio_source = discord.FFmpegPCMAudio(BUZZER_SOUND)
                if not vc.is_playing():
                    vc.play(audio_source)
                    while vc.is_playing():
                        await asyncio.sleep(0.5)

                await vc.disconnect()

            except Exception as e:
                print(f"⚠️ Error playing sound: {e}")
                await interaction.followup.send("⚠️ Couldn't play the buzz sound.", ephemeral=True)

        else:
            await interaction.response.send_message("❌ You must be in a voice channel to buzz!", ephemeral=True)
            return

        # 📣 Announce winner in a text channel
        results_channel = discord.utils.get(interaction.guild.text_channels, name="game-show")
        if results_channel:
            await results_channel.send(f"🔔 **{first_buzzer}** buzzed in first!")

@bot.command()
@commands.has_role("Admin")  # Only users with Admin role can use this
async def start_buzzer(ctx):
    """Start a new round."""
    global buzzer_locked, first_buzzer

    buzzer_locked = False
    first_buzzer = None
    view = BuzzerView()
    await ctx.send("🚨 Press the **Buzz!** button when you're ready!", view=view)

@bot.command()
@commands.has_role("Admin")
async def reset_buzzer(ctx):
    """Reset for the next round."""
    await start_buzzer(ctx)

bot.run(TOKEN)
