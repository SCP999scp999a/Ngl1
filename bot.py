import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import string

# ================== CONFIG ==================
TOKEN = os.environ.get("TOKEN")

ALLOWED_CHANNEL_ID = 1463714560816058654
BACKEND_CHANNEL_ID = 1463722599468105972
VOICE_CHANNEL_ID = 1434155735704408117
# ============================================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== UTIL ==================
def random_device_id(length=16):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def extract_username(link):
    if "ngl.link/" not in link:
        return None
    return link.split("ngl.link/")[-1].strip("/")

# ================== NGL SENDER ==================
async def send_ngl_async(channel, backend_channel, user, username, text, count, delay, link):
    url = "https://ngl.link/api/submit"
    headers = {"Content-Type": "application/json"}

    success = 0
    fail = 0

    embed = discord.Embed(
        title="📤 กำลังส่ง NGL",
        description="เริ่มงาน...",
        color=0x00ff99
    )
    status_msg = await channel.send(embed=embed)

    async with aiohttp.ClientSession(headers=headers) as session:
        for i in range(count):
            payload = {
                "username": username,
                "question": text,
                "deviceId": random_device_id(),
                "gameSlug": "",
                "referrer": ""
            }

            try:
                async with session.post(url, json=payload, timeout=15) as r:
                    if r.status == 200:
                        success += 1
                    else:
                        fail += 1
            except:
                fail += 1

            embed.description = f"รอบ {i+1}/{count}\n✅ {success} | ❌ {fail}"
            await status_msg.edit(embed=embed)

            if i + 1 < count:
                await asyncio.sleep(delay)

    embed.title = "✅ เสร็จสิ้น"
    await status_msg.edit(embed=embed)

# ================== MODAL ==================
class NGLModal(discord.ui.Modal, title="ส่ง NGL"):
    link = discord.ui.TextInput(label="ลิงก์ NGL")
    message = discord.ui.TextInput(label="ข้อความ")
    count = discord.ui.TextInput(label="จำนวนครั้ง")
    delay = discord.ui.TextInput(label="หน่วงวินาที (>=0.5)")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            count = int(self.count.value)
            delay = float(self.delay.value)
            assert count > 0 and delay >= 0.5
        except:
            return await interaction.followup.send("❌ ค่าผิด", ephemeral=True)

        username = extract_username(self.link.value)
        if not username:
            return await interaction.followup.send("❌ ลิงก์ผิด", ephemeral=True)

        backend = bot.get_channel(BACKEND_CHANNEL_ID)

        asyncio.create_task(
            send_ngl_async(
                interaction.channel,
                backend,
                interaction.user,
                username,
                self.message.value,
                count,
                delay,
                self.link.value
            )
        )

        await interaction.followup.send("✅ เริ่มแล้ว", ephemeral=True)

# ================== VIEW ==================
class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="เปิดเมนูส่ง NGL", style=discord.ButtonStyle.success)
    async def open_menu(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(NGLModal())

# ================== EVENTS ==================
@bot.event
async def on_ready():
    bot.add_view(MenuView())
    print(f"✅ Bot Ready : {bot.user}")

    # เข้า Voice อัตโนมัติ
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if isinstance(channel, discord.VoiceChannel):
        try:
            await channel.connect()
            print("🎤 เข้า Voice แล้ว")
        except:
            pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == ALLOWED_CHANNEL_ID and message.content == "พิมพ์":
        await message.delete()

        embed = discord.Embed(
            title="📨 ระบบส่ง NGL",
            description="กดปุ่มด้านล่าง",
            color=0x5865F2
        )

        await message.channel.send(embed=embed, view=MenuView())

    await bot.process_commands(message)

# ================== RUN ==================
if not TOKEN:
    raise RuntimeError("❌ ไม่พบ TOKEN")

bot.run(TOKEN)
