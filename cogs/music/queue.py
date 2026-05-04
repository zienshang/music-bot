"""
cogs/music/queue.py
─────────────────────────────────────────────────────────────────────────────
EN: Queue viewer with paginated navigation. Shows the currently playing
    track and up to 10 queued tracks per page. The embed auto-deletes
    after 130 seconds of inactivity via on_timeout.
VI: Trình xem queue với điều hướng phân trang. Hiển thị bài đang phát
    và tối đa 10 bài trong queue mỗi trang. Embed tự xóa sau 130 giây
    không hoạt động qua on_timeout.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import discord
import wavelink


class QueueView(discord.ui.View):
    """
    EN: Paginated view with ◀️ / ▶️ buttons for navigating the queue.
        Stores a reference to its own message so on_timeout can delete it.
    VI: View phân trang với nút ◀️ / ▶️ để điều hướng queue.
        Lưu tham chiếu đến message của nó để on_timeout có thể xóa.
    """

    def __init__(self, cog, player, page=1):
        super().__init__(timeout=130)  # EN: 130 s inactivity before cleanup / VI: 130 giây không tương tác thì dọn dẹp
        self.cog    = cog
        self.player = player
        self.page   = page
        self.message: discord.Message = None  # EN: set after send() returns / VI: gán sau khi send() trả về

    @property
    def total_pages(self):
        """
        EN: Calculate total page count based on queue length (10 tracks/page).
            Returns at least 1 so the footer always shows a valid page number.
        VI: Tính tổng số trang dựa trên độ dài queue (10 bài/trang).
            Trả về ít nhất 1 để footer luôn hiển thị số trang hợp lệ.
        """
        return max(1, (self.player.queue.count + 9) // 10)

    async def on_timeout(self):
        """
        EN: Called by discord.py when no button interaction occurs within
            `timeout` seconds. Silently deletes the queue message.
        VI: Được gọi bởi discord.py khi không có tương tác nút nào xảy ra
            trong `timeout` giây. Im lặng xóa message queue.
        """
        if self.message:
            try:
                await self.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, _):
        """
        EN: Navigate to the previous page (clamps at page 1).
        VI: Điều hướng đến trang trước (giới hạn tối thiểu trang 1).
        """
        if self.page > 1:
            self.page -= 1
        await interaction.response.edit_message(
            embed=self.cog.build_embed(self.player, self.page, self.total_pages),
            view=self
        )

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.grey)
    async def next_p(self, interaction: discord.Interaction, _):
        """
        EN: Navigate to the next page (clamps at last page).
        VI: Điều hướng đến trang tiếp theo (giới hạn tối đa trang cuối).
        """
        if self.page < self.total_pages:
            self.page += 1
        await interaction.response.edit_message(
            embed=self.cog.build_embed(self.player, self.page, self.total_pages),
            view=self
        )


class Queue(commands.Cog, name="Queue"):
    def __init__(self, bot):
        self.bot = bot

    def build_embed(self, player, page, total_pages) -> Embed:
        """
        EN: Build the queue embed for a given page. Shows:
              • Currently playing track (always at top)
              • Up to 10 upcoming tracks for the requested page
              • Page indicator in the footer
        VI: Tạo embed queue cho trang đã cho. Hiển thị:
              • Bài đang phát (luôn ở trên cùng)
              • Tối đa 10 bài tiếp theo cho trang yêu cầu
              • Chỉ báo trang ở footer
        """
        per_page = 10
        start  = (page - 1) * per_page
        tracks = list(player.queue)[start:start + per_page]

        embed = Embed(title=f"📋 Queue — {player.queue.count} bài", color=Colour.blue())

        if player.current:
            embed.add_field(
                name="▶️ Đang phát",
                value=f"**[{player.current.title[:55]}]({player.current.uri})**",
                inline=False
            )

        if tracks:
            # EN: Numbered list with hyperlinked titles for easy identification.
            # VI: Danh sách đánh số với tiêu đề có liên kết để dễ nhận biết.
            desc = "\n".join(
                f"`{i+start+1:2d}.` [{t.title[:48]}]({t.uri})"
                for i, t in enumerate(tracks)
            )
            embed.add_field(name="📋 Tiếp theo", value=desc, inline=False)

        embed.set_footer(text=f"Trang {page}/{total_pages} • Tự xóa sau 130 giây")
        return embed

    @commands.command(aliases=['q', 'qu'], help="Xem danh sách phát")
    async def queue(self, ctx):
        """
        EN: Display the current queue. If empty and nothing is playing, show an
            "empty queue" message. Otherwise send a paginated embed.
        VI: Hiển thị queue hiện tại. Nếu trống và không có gì phát, hiển thị
            thông báo "queue trống". Nếu không, gửi embed phân trang.
        """
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send(embed=Embed(title="❌ Bot chưa vào voice!", color=Colour.red()))
        if player.queue.is_empty and not player.current:
            return await ctx.send(embed=Embed(title="📭 Queue trống!", color=Colour.orange()))

        view = QueueView(self, player)
        msg  = await ctx.send(embed=self.build_embed(player, 1, view.total_pages), view=view)
        # EN: Give the view a reference so on_timeout can delete this message.
        # VI: Gán tham chiếu cho view để on_timeout có thể xóa message này.
        view.message = msg


async def setup(bot):
    await bot.add_cog(Queue(bot))
