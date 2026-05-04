"""
cogs/music/play.py
─────────────────────────────────────────────────────────────────────────────
EN: Core playback Cog. Handles the -play command and the wavelink track
    lifecycle events (track start / track end) that drive the queue.
VI: Cog phát nhạc cốt lõi. Xử lý lệnh -play và các sự kiện vòng đời
    track của wavelink (bắt đầu/kết thúc track) để điều khiển queue.
─────────────────────────────────────────────────────────────────────────────
"""

from discord.ext import commands
from discord import Embed, Colour
import discord
import wavelink
import asyncio
from utils.helpers import get_source
from utils.nowplaying import NowPlayingManager

# EN: Module-level singleton so the manager's message/task state persists
#     across multiple command invocations within the same bot session.
# VI: Singleton ở cấp module để trạng thái message/task của manager tồn tại
#     qua nhiều lần gọi lệnh trong cùng một phiên bot.
npm = NowPlayingManager()


class Play(commands.Cog, name="Play"):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────────────────
    @commands.command(aliases=['p', 'pl'], help="Phát nhạc từ YouTube, Spotify, SoundCloud")
    async def play(self, ctx, *, search: str):
        """
        EN: Main play command. Behaviour depends on current player state:
              • Not in voice → bot joins the caller's channel first.
              • Not playing  → play immediately, send Now Playing embed.
              • Already playing → add to queue, show "added to queue" card,
                                  auto-delete after 30 seconds.
            Supports single tracks AND playlists from YouTube/Spotify/SoundCloud.
        VI: Lệnh phát nhạc chính. Hành vi phụ thuộc trạng thái player hiện tại:
              • Chưa vào voice → bot vào kênh của người gọi trước.
              • Chưa phát      → phát ngay, gửi embed Now Playing.
              • Đang phát      → thêm vào queue, hiển thị thẻ "đã thêm queue",
                                  tự xóa sau 30 giây.
            Hỗ trợ cả bài đơn lẫn playlist từ YouTube/Spotify/SoundCloud.
        """
        # EN: Guard — user must be in a voice channel to use this command.
        # VI: Kiểm tra — người dùng phải ở trong voice channel.
        if not ctx.author.voice:
            return await ctx.send(embed=Embed(title="❌ Bạn chưa vào voice!", color=Colour.red()))

        # EN: Connect to voice if not already connected.
        # VI: Kết nối vào voice nếu chưa kết nối.
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect(cls=wavelink.Player)

        player: wavelink.Player = ctx.voice_client

        # EN: Detect the platform so the embed colour matches the source.
        # VI: Phát hiện nền tảng để màu embed khớp với nguồn.
        if any(x in search for x in ("spotify.com", "open.spotify")):
            source_icon, source_color = "🎵 Spotify", Colour.green()
        elif search.startswith("spsearch:"):
            source_icon, source_color = "🎵 Spotify", Colour.green()
        elif any(x in search for x in ("soundcloud.com", "scsearch:")):
            source_icon, source_color = "🔊 SoundCloud", Colour.orange()
        else:
            source_icon, source_color = "▶️ YouTube", Colour.red()

        # EN: Send a "searching…" placeholder while the API call is in-flight.
        # VI: Gửi thông báo "đang tìm kiếm…" trong khi chờ API trả về.
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
            return await msg.edit(embed=Embed(
                title="❌ Không tìm thấy",
                description=f"`{search[:60]}`",
                color=Colour.red()
            ))

        # ── Playlist branch ────────────────────────────────────────────────
        if isinstance(tracks, wavelink.Playlist):
            playlist = tracks
            if not playlist.tracks:
                return await msg.edit(embed=Embed(title="❌ Playlist trống!", color=Colour.red()))

            # EN: Enqueue the entire playlist at once.
            # VI: Thêm toàn bộ playlist vào queue cùng lúc.
            await player.queue.put_wait(playlist)
            total = len(playlist.tracks)

            # EN: Show a 3-track preview so the user knows what's queued.
            # VI: Hiển thị xem trước 3 bài để người dùng biết queue có gì.
            preview = "\n".join(
                f"`{i+1}.` **{t.title[:40]}**"
                for i, t in enumerate(playlist.tracks[:3])
            )
            if total > 3:
                preview += f"\n➕ *+{total-3} bài khác*"

            embed = Embed(
                title="➕ Playlist đã thêm!",
                description=f"**📀 {playlist.name[:60]}**\n🎵 {total} bài • {source_icon}",
                color=source_color
            )
            embed.add_field(name="📋 Preview", value=preview, inline=False)
            thumb = getattr(playlist.tracks[0], 'artwork', None)
            if thumb:
                embed.set_thumbnail(url=thumb)
            await msg.edit(embed=embed)

            # EN: Start playback if nothing is playing yet.
            # VI: Bắt đầu phát nếu chưa có gì đang phát.
            if not player.playing:
                track = player.queue.get()
                await player.play(track)
                await msg.delete()
                await npm.send(ctx, player, track)

        # ── Single track branch ────────────────────────────────────────────
        else:
            track = tracks[0]

            if player.playing:
                # EN: Bot is already playing — add to queue and show a card
                #     that self-deletes after 30 seconds to reduce clutter.
                # VI: Bot đang phát — thêm vào queue và hiển thị thẻ
                #     tự xóa sau 30 giây để giảm lộn xộn kênh chat.
                await player.queue.put_wait(track)
                embed = Embed(
                    title="➕ Đã thêm queue",
                    description=f"**{track.title[:70]}**\n👤 {track.author} • {source_icon}",
                    color=source_color
                )
                embed.add_field(name="Vị trí", value=f"#{player.queue.count}", inline=True)
                thumb = getattr(track, 'artwork', None)
                if thumb:
                    embed.set_thumbnail(url=thumb)
                await msg.edit(embed=embed)

                await asyncio.sleep(30)
                try:
                    await msg.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass  # EN: already deleted, that's fine / VI: đã bị xóa rồi, không sao
            else:
                # EN: Nothing playing — start immediately and show Now Playing.
                # VI: Không có gì đang phát — bắt đầu ngay và hiển thị Now Playing.
                await player.play(track)
                await msg.delete()
                await npm.send(ctx, player, track)

    # ─── wavelink event: track started ────────────────────────────────────
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """
        EN: When a new track starts (including auto-advance from queue),
            update the Now Playing embed with the new track's info.
        VI: Khi bài mới bắt đầu (kể cả tự động chuyển từ queue),
            cập nhật embed Now Playing với thông tin bài mới.
        """
        player = payload.player
        if not player or not player.guild:
            return
        await npm.update(player.guild.id, player, payload.track)

    # ─── wavelink event: track ended ──────────────────────────────────────
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """
        EN: When a track ends, play the next one from the queue (if any).
            If the queue is empty, tell NowPlayingManager to clean up.
        VI: Khi bài kết thúc, phát bài tiếp theo trong queue (nếu có).
            Nếu queue trống, báo NowPlayingManager dọn dẹp.
        """
        player = payload.player
        if not player:
            return
        if not player.queue.is_empty:
            # EN: Dequeue the next track and start it immediately.
            # VI: Lấy bài tiếp theo khỏi queue và phát ngay.
            await player.play(player.queue.get())
        else:
            await npm.stop(player.guild.id)


async def setup(bot):
    await bot.add_cog(Play(bot))
