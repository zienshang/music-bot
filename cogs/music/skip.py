"""
cogs/music/skip.py
─────────────────────────────────────────────────────────────────────────────
EN: Skip command. Calls wavelink's built-in skip(), which internally stops
    the current track and fires on_wavelink_track_end so play.py's listener
    automatically starts the next queued track.
VI: Lệnh skip. Gọi skip() tích hợp của wavelink, nội bộ dừng bài hiện tại
    và kích hoạt on_wavelink_track_end để listener trong play.py
    tự động phát bài tiếp theo trong queue.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink
import asyncio
import discord


class Skip(commands.Cog, name="Skip"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['s', 'sk'], help="Bỏ qua bài đang phát")
    async def skip(self, ctx):
        """
        EN: Skip the currently playing track.
            The confirmation message auto-deletes after 5 seconds to keep chat tidy.
        VI: Bỏ qua bài đang phát.
            Thông báo xác nhận tự xóa sau 5 giây để giữ kênh chat gọn gàng.
        """
        player: wavelink.Player = ctx.voice_client
        if not player or not player.playing:
            return await ctx.send(
                embed=Embed(title="❌ Không có bài đang phát!", color=Colour.red()),
                delete_after=5
            )

        # EN: wavelink.skip() triggers on_wavelink_track_end automatically.
        # VI: wavelink.skip() tự kích hoạt on_wavelink_track_end.
        await player.skip()
        await ctx.send(
            embed=Embed(title="⏭ Đã skip!", color=Colour.blurple()),
            delete_after=5
        )


async def setup(bot):
    await bot.add_cog(Skip(bot))
