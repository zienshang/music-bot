"""
cogs/music/leave.py
─────────────────────────────────────────────────────────────────────────────
EN: Leave command. Clears the queue and disconnects the bot from the voice
    channel. The voice status cleanup is handled separately by StatusManager
    via the on_voice_state_update event.
VI: Lệnh leave. Xóa queue và ngắt kết nối bot khỏi voice channel.
    Việc dọn dẹp trạng thái voice được xử lý riêng bởi StatusManager
    thông qua sự kiện on_voice_state_update.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink


class Leave(commands.Cog, name="Leave"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['dc', 'disconnect'], help="Bot rời voice channel")
    async def leave(self, ctx):
        """
        EN: Clear the queue and disconnect the bot.
            The confirmation auto-deletes after 5 seconds.
            Note: NowPlayingManager cleanup happens via on_wavelink_track_end
            in play.py when the track is stopped.
        VI: Xóa queue và ngắt kết nối bot.
            Xác nhận tự xóa sau 5 giây.
            Lưu ý: Dọn dẹp NowPlayingManager xảy ra qua on_wavelink_track_end
            trong play.py khi bài bị dừng.
        """
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send(embed=Embed(title="❌ Bot chưa vào voice!", color=Colour.red()))

        # EN: Clear the queue first so on_wavelink_track_end doesn't start the next track.
        # VI: Xóa queue trước để on_wavelink_track_end không phát bài tiếp theo.
        player.queue.clear()
        await player.disconnect()
        await ctx.send(
            embed=Embed(title="👋 Đã rời voice!", color=Colour.orange()),
            delete_after=5
        )


async def setup(bot):
    await bot.add_cog(Leave(bot))
