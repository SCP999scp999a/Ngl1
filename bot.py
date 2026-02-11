import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import string

TOKEN = os.environ.get("TOKEN")
ALLOWED_CHANNEL_ID = 1463714560816058654
BACKEND_CHANNEL_ID = 1463722599468105972
# ============================================

intents = discord.Intents.default()
intents.message_content = True

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
        description="กำลังเริ่มงาน...",
        color=0x00ff99
    )
    status_msg = await channel.send(embed=embed)

    await backend_channel.send(
        f"📥 งานใหม่\n"
        f"👤 {user}\n"
        f"🔗 {link}\n"
        f"💬 {text}\n"
        f"🔢 {count}\n"
        f"⏱ {delay}s"
    )

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

            embed.description = (
                f"รอบ {i+1}/{count}\n"
                f"✅ สำเร็จ: {success}\n"
                f"❌ ล้มเหลว: {fail}"
            )
            await status_msg.edit(embed=embed)

            if i + 1 < count:
                await asyncio.sleep(delay)

    embed.title = "✅ เสร็จสิ้น"
    await status_msg.edit(embed=embed)

# ================== MODAL ==================
class NGLModal(discord.ui.Modal, title="เมนูส่ง NGL"):
    link = discord.ui.TextInput(label="ลิงก์ NGL", placeholder="https://ngl.link/username")
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
            return await interaction.followup.send("❌ ค่าที่กรอกไม่ถูกต้อง", ephemeral=True)

        username = extract_username(self.link.value)
        if not username:
            return await interaction.followup.send("❌ ลิงก์ NGL ไม่ถูกต้อง", ephemeral=True)

        backend_channel = bot.get_channel(BACKEND_CHANNEL_ID)

        asyncio.create_task(
            send_ngl_async(
                interaction.channel,
                backend_channel,
                interaction.user,
                username,
                self.message.value,
                count,
                delay,
                self.link.value
            )
        )

        await interaction.followup.send("✅ เริ่มส่งแล้ว", ephemeral=True)

# ================== VIEW (PERSISTENT) ==================
class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="เปิดเมนูส่ง NGL",
        style=discord.ButtonStyle.success,
        custom_id="ngl_open_menu"
    )
    async def open_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NGLModal())

# ================== EVENTS ==================
@bot.event
async def on_ready():
    bot.add_view(MenuView())
    print(f"Bot Ready | Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == ALLOWED_CHANNEL_ID and message.content == "พิมพ์":
        await message.delete()

        embed = discord.Embed(
            title="📨 ระบบส่ง NGL",
            description="กดปุ่มด้านล่างเพื่อเปิดเมนู",
            color=0x5865F2
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1427659460679045303/1464106538682552581/ae72f063d21a02434145ea696433bdff.jpg?ex=697442f8&is=6972f178&hm=9f32ce734aed873e545ee4e8ec7a0cf35ddcfdc6fa634196177444e5a698bd79")
        embed.set_image(url="https://cdn.discordapp.com/attachments/1427659460679045303/1464101713060561102/nwboy8jcdUA840zDQpL-o.jpg?ex=69743e7a&is=6972ecfa&hm=b1126b9b96d439b3a5ac6b9271a4e0e38b6364507a3e049d3a299d37e4b8bbfd")  # เปลี่ยนเป็นรูปของคุณได้

        await message.channel.send(embed=embed, view=MenuView())

    await bot.process_commands(message)




bot.run(TOKEN)


import discord
import asyncio

VOICE_CHANNEL_ID = 1434155735704408117  # ใส่ ID ช่องเสียง
voice_client = None


async def auto_join_voice():
    global voice_client

    await bot.wait_until_ready()

    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(VOICE_CHANNEL_ID)
        except:
            print("❌ ดึงช่องเสียงไม่สำเร็จ")
            return

    if not isinstance(channel, discord.VoiceChannel):
        print("❌ ID นี้ไม่ใช่ช่องเสียง")
        return

    try:
        if voice_client and voice_client.is_connected():
            return

        voice_client = await channel.connect()
        print("✅ บอทเข้า Voice แล้ว")

    except Exception as e:
        print("❌ เข้า Voice ไม่ได้:", e)


bot.loop.create_task(auto_join_voice())


@bot.event
async def on_ready():
    # โค้ดเดิมของคุณ (ถ้ามี)

    channel = bot.get_channel(1464187102181982239)
    print(f"หาช่อง: {channel}")  # เช็คว่าหาช่องเจอไหม

    if channel and isinstance(channel, discord.VoiceChannel):
        try:
            await channel.connect()
            print("เข้าช่องเสียงแล้ว!")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("ไม่เจอช่องหรือไม่ใช่ Voice Channel")
                        
