"""
cogs/music/clear_queue.py
─────────────────────────────────────────────────────────────────────────────
EN: Clear Queue command. Empties all upcoming tracks without stopping the
    currently playing track. Useful when the user wants to start fresh
    without interrupting the current song.
VI: Lệnh xóa queue. Xóa tất cả bài sắp tới mà không dừng bài đang phát.
    Hữu ích khi người dùng muốn bắt đầu lại từ đầu mà không làm gián đoạn
    bài hiện tại.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink


class ClearQueue(commands.Cog, name="ClearQueue"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", aliases=['cl', 'clq', 'clearqueue'], help="Xóa toàn bộ queue")
    async def clear(self, ctx):
        """
        EN: Remove all tracks from the queue (does not stop the current track).
            Reports how many tracks were removed. Both responses auto-delete
            to keep the chat clean.
        VI: Xóa tất cả bài khỏi queue (không dừng bài đang phát).
            Báo cáo số bài đã bị xóa. Cả hai phản hồi đều tự xóa
            để giữ kênh chat sạch sẽ.
        """
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send(
                embed=Embed(title="❌ Bot chưa vào voice!", color=Colour.red()),
                delete_after=5
            )
        if player.queue.is_empty:
            return await ctx.send(
                embed=Embed(title="📭 Queue đang trống!", color=Colour.orange()),
                delete_after=5
            )

        # EN: Capture count before clearing so we can report it accurately.
        # VI: Lưu số lượng trước khi xóa để có thể báo cáo chính xác.
        count = player.queue.count
        player.queue.clear()
        await ctx.send(
            embed=Embed(title=f"🗑️ Đã xóa {count} bài khỏi queue!", color=Colour.green()),
            delete_after=10
        )


async def setup(bot):
    await bot.add_cog(ClearQueue(bot))
