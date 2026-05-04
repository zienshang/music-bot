"""
cogs/music/shuffle.py
─────────────────────────────────────────────────────────────────────────────
EN: Shuffle command. Randomises the order of tracks currently in the queue
    without affecting the track that is already playing.
VI: Lệnh shuffle. Xáo trộn ngẫu nhiên thứ tự các bài trong queue
    mà không ảnh hưởng đến bài đang phát.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink


class Shuffle(commands.Cog, name="Shuffle"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['sh'], help="Trộn ngẫu nhiên queue")
    async def shuffle(self, ctx):
        """
        EN: Shuffle the upcoming queue in-place using wavelink's built-in
            queue.shuffle(). Confirmation auto-deletes after 10 seconds.
        VI: Xáo trộn queue tiếp theo tại chỗ bằng queue.shuffle() của wavelink.
            Xác nhận tự xóa sau 10 giây.
        """
        player: wavelink.Player = ctx.voice_client
        if not player or player.queue.is_empty:
            return await ctx.send(embed=Embed(title="📭 Queue trống!", color=Colour.orange()))

        player.queue.shuffle()
        await ctx.send(
            embed=Embed(title="🔀 Đã trộn queue!", color=Colour.green()),
            delete_after=10
        )


async def setup(bot):
    await bot.add_cog(Shuffle(bot))
