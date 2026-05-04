"""
cogs/music/addtrack.py
─────────────────────────────────────────────────────────────────────────────
EN: Adds a track (or playlist) to the queue WITHOUT starting playback.
    Useful when the user wants to pre-load songs while something is playing.
VI: Thêm bài nhạc (hoặc playlist) vào queue MÀ KHÔNG bắt đầu phát.
    Hữu ích khi người dùng muốn thêm bài trước trong khi đang phát nhạc.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import wavelink
from utils.helpers import get_source


class AddTrack(commands.Cog, name="AddTrack"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['at', 'add'], help="Thêm bài vào queue (không phát ngay)")
    async def addtrack(self, ctx, *, search: str):
        """
        EN: Search for a track/playlist and append it to the queue.
            Unlike -play, this never starts playback — it only enqueues.
            Requires the bot to already be playing (voice connected).
        VI: Tìm kiếm bài nhạc/playlist và thêm vào cuối queue.
            Khác với -play, lệnh này không bao giờ bắt đầu phát — chỉ thêm vào queue.
            Yêu cầu bot đang phát nhạc (đã kết nối voice).
        """
        if not ctx.author.voice:
            return await ctx.send(embed=Embed(title="❌ Bạn chưa vào voice!", color=Colour.red()))
        if not ctx.voice_client:
            # EN: Bot must already be in voice — use -play to start a new session.
            # VI: Bot phải đã ở trong voice — dùng -play để bắt đầu phiên mới.
            return await ctx.send(embed=Embed(title="❌ Bot chưa phát nhạc! Dùng -play trước.", color=Colour.red()))

        player: wavelink.Player = ctx.voice_client
        source_icon, source_color = get_source(search)

        msg = await ctx.send(embed=Embed(
            title="🔍 Đang tìm kiếm...",
            description=f"`{search[:60]}`",
            color=Colour.yellow()
        ))

        try:
            tracks = await wavelink.Playable.search(search)
        except Exception as e:
            return await msg.edit(embed=Embed(title="❌ Lỗi tìm kiếm", description=f"`{e}`", color=Colour.red()))

        if not tracks:
            return await msg.edit(embed=Embed(title="❌ Không tìm thấy", color=Colour.red()))

        if isinstance(tracks, wavelink.Playlist):
            # EN: Enqueue all tracks in the playlist at once.
            # VI: Thêm tất cả bài trong playlist vào queue cùng lúc.
            await player.queue.put_wait(tracks)
            embed = Embed(
                title="➕ Đã thêm playlist",
                description=f"**{tracks.name}** — {len(tracks.tracks)} bài • {source_icon}",
                color=source_color
            )
        else:
            track = tracks[0]
            await player.queue.put_wait(track)
            embed = Embed(
                title="➕ Đã thêm vào queue",
                description=f"**{track.title[:70]}**\n👤 {track.author} • {source_icon}",
                color=source_color
            )
            # EN: Show queue position so the user knows how long they'll wait.
            # VI: Hiển thị vị trí trong queue để người dùng biết phải chờ bao lâu.
            embed.add_field(name="Vị trí", value=f"#{player.queue.count}", inline=True)
            thumb = getattr(track, 'artwork', None)
            if thumb:
                embed.set_thumbnail(url=thumb)

        await msg.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(AddTrack(bot))
