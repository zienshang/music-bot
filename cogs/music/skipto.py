"""
cogs/music/skipto.py
─────────────────────────────────────────────────────────────────────────────
EN: Skip To command. Jumps directly to a specific position in the queue,
    discarding all tracks before it. The target track starts playing
    immediately without interrupting the overall playback flow.
VI: Lệnh Skip To. Nhảy trực tiếp đến vị trí cụ thể trong queue,
    loại bỏ tất cả bài trước đó. Bài đích bắt đầu phát ngay lập tức
    mà không làm gián đoạn luồng phát nhạc tổng thể.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink


class SkipTo(commands.Cog, name="SkipTo"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="skipto", aliases=["st", "goto"], help="Nhảy đến bài thứ N trong queue")
    async def skipto(self, ctx, position: int):
        """
        EN: Skip directly to a track at the given queue position (1-based index).
            All tracks before that position are removed from the queue.
            The chosen track then becomes the next to play via player.skip().

            Example: -skipto 3  →  discards tracks #1 and #2, plays #3 next.

        VI: Nhảy trực tiếp đến bài ở vị trí đã cho trong queue (chỉ số từ 1).
            Tất cả bài trước vị trí đó bị xóa khỏi queue.
            Bài được chọn sau đó trở thành bài tiếp theo phát qua player.skip().

            Ví dụ: -skipto 3  →  xóa bài #1 và #2, phát bài #3 tiếp theo.
        """
        player: wavelink.Player = ctx.voice_client

        # EN: Guard — bot must be connected and playing.
        # VI: Kiểm tra — bot phải đang kết nối và phát nhạc.
        if not player or not player.playing:
            return await ctx.send(
                embed=Embed(title="❌ Không có bài đang phát!", color=Colour.red()),
                delete_after=5
            )

        # EN: Guard — queue must have tracks to skip to.
        # VI: Kiểm tra — queue phải có bài để nhảy tới.
        if player.queue.is_empty:
            return await ctx.send(
                embed=Embed(title="📭 Queue đang trống!", color=Colour.orange()),
                delete_after=5
            )

        queue_len = player.queue.count

        # EN: Validate the requested position is within bounds (1 to queue length).
        # VI: Kiểm tra vị trí yêu cầu nằm trong phạm vi hợp lệ (1 đến độ dài queue).
        if position < 1 or position > queue_len:
            return await ctx.send(
                embed=Embed(
                    title="❌ Vị trí không hợp lệ!",
                    description=(
                        f"🇬🇧 Please enter a number between `1` and `{queue_len}`.\n"
                        f"🇻🇳 Vui lòng nhập số từ `1` đến `{queue_len}`."
                    ),
                    color=Colour.red()
                ),
                delete_after=8
            )

        # EN: Grab the target track's info BEFORE mutating the queue,
        #     so we can display it in the confirmation embed.
        # VI: Lấy thông tin bài đích TRƯỚC khi thay đổi queue,
        #     để hiển thị trong embed xác nhận.
        queue_list = list(player.queue)
        target_track = queue_list[position - 1]

        # EN: Remove all tracks that come before the target position.
        #     We pop (position - 1) times from the front of the queue.
        # VI: Xóa tất cả bài đứng trước vị trí đích.
        #     Lấy ra (position - 1) lần từ đầu queue.
        for _ in range(position - 1):
            player.queue.get()

        # EN: Skip the current track — wavelink fires on_wavelink_track_end,
        #     which in play.py pulls the next item (our target) from the queue
        #     and starts it automatically.
        # VI: Bỏ qua bài hiện tại — wavelink kích hoạt on_wavelink_track_end,
        #     trong play.py lấy item tiếp theo (bài đích) từ queue
        #     và tự động phát.
        await player.skip()

        embed = Embed(
            title=f"⏩ Đã nhảy đến bài #{position}",
            description=f"**{target_track.title[:70]}**\n👤 {target_track.author}",
            color=Colour.blurple()
        )
        embed.add_field(
            name="🗑️ Đã bỏ qua / Skipped",
            value=(
                f"🇻🇳 `{position - 1}` bài trước đó\n"
                f"🇬🇧 `{position - 1}` track(s) before it"
            ),
            inline=False
        )
        thumb = getattr(target_track, 'artwork', None)
        if thumb:
            embed.set_thumbnail(url=thumb)

        await ctx.send(embed=embed, delete_after=30)


async def setup(bot):
    await bot.add_cog(SkipTo(bot))
