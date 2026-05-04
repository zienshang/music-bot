"""
cogs/music/volume.py
─────────────────────────────────────────────────────────────────────────────
EN: Volume command. Lets users set the playback volume from 0 to 1000.
    Lavalink supports beyond 100% (amplification); anything above ~150
    may cause audio clipping depending on the source.
VI: Lệnh volume. Cho phép người dùng đặt âm lượng phát từ 0 đến 1000.
    Lavalink hỗ trợ vượt 100% (khuếch đại); trên ~150 có thể gây
    vỡ tiếng tùy nguồn âm thanh.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink


class Volume(commands.Cog, name="Volume"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['vol', 'v'], help="Chỉnh âm lượng (0-1000)")
    async def volume(self, ctx, vol: int):
        """
        EN: Set the player volume. The value is clamped to [0, 1000] so
            out-of-range inputs are silently corrected rather than raising
            an error. A simple emoji bar gives visual volume feedback.
        VI: Đặt âm lượng player. Giá trị được kẹp trong [0, 1000] để
            đầu vào ngoài phạm vi được tự động sửa thay vì báo lỗi.
            Thanh emoji đơn giản cung cấp phản hồi âm lượng trực quan.
        """
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send(embed=Embed(title="❌ Bot chưa vào voice!", color=Colour.red()))

        # EN: Clamp to valid range — avoids exceptions from out-of-bound values.
        # VI: Kẹp trong phạm vi hợp lệ — tránh exception từ giá trị ngoài giới hạn.
        vol = max(0, min(vol, 1000))
        await player.set_volume(vol)

        # EN: Visual bar: 1 🔊 per 100 units, padded with ▁ to always be 10 wide.
        # VI: Thanh trực quan: 1 🔊 mỗi 100 đơn vị, đệm bằng ▁ để luôn rộng 10 ký tự.
        bar = "🔊" * (vol // 100) + "▁" * (10 - vol // 100)
        await ctx.send(
            embed=Embed(title=f"🔊 Volume: {vol}%", description=bar, color=Colour.blurple()),
            delete_after=10
        )


async def setup(bot):
    await bot.add_cog(Volume(bot))
