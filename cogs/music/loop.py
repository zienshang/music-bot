"""
cogs/music/loop.py
─────────────────────────────────────────────────────────────────────────────
EN: Loop command. Cycles the queue's loop mode through three states:
      Normal (no loop) → Loop Track → Loop All → Normal …
    wavelink's QueueMode drives the actual playback behaviour; this Cog
    simply advances the state and reports it to the user.
VI: Lệnh loop. Xoay vòng chế độ lặp queue qua ba trạng thái:
      Thường (không lặp) → Lặp bài → Lặp tất cả → Thường …
    QueueMode của wavelink điều khiển hành vi phát thực tế; Cog này
    chỉ đơn giản chuyển trạng thái và thông báo cho người dùng.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink


class Loop(commands.Cog, name="Loop"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['l', 'lp'], help="Bật/tắt loop (Tắt → Bài → Tất cả)")
    async def loop(self, ctx):
        """
        EN: Advance the loop mode by one step and notify the user.
            Confirmation auto-deletes after 10 seconds.
              QueueMode.normal   → QueueMode.loop     (single-track repeat)
              QueueMode.loop     → QueueMode.loop_all (repeat entire queue)
              QueueMode.loop_all → QueueMode.normal   (disable loop)
        VI: Chuyển chế độ lặp lên một bước và thông báo cho người dùng.
            Xác nhận tự xóa sau 10 giây.
              QueueMode.normal   → QueueMode.loop     (lặp bài hiện tại)
              QueueMode.loop     → QueueMode.loop_all (lặp toàn bộ queue)
              QueueMode.loop_all → QueueMode.normal   (tắt lặp)
        """
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send(embed=Embed(title="❌ Bot chưa vào voice!", color=Colour.red()))

        if player.queue.mode == wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.loop
            label, color = "🔂 Loop: Bài hiện tại", Colour.green()
        elif player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.loop_all
            label, color = "🔁 Loop: Tất cả", Colour.blue()
        else:
            player.queue.mode = wavelink.QueueMode.normal
            label, color = "➡️ Loop: Tắt", Colour.grey()

        await ctx.send(embed=Embed(title=label, color=color), delete_after=10)


async def setup(bot):
    await bot.add_cog(Loop(bot))
