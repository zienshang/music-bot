"""
utils/nowplaying.py
─────────────────────────────────────────────────────────────────────────────
EN: Now-Playing system: builds the embed, handles interactive buttons,
    and manages a per-guild background task that refreshes the embed
    every 30 seconds and re-sends it every 5 minutes to keep it visible.
VI: Hệ thống Now-Playing: tạo embed, xử lý các nút tương tác,
    và quản lý tác vụ nền theo từng guild để làm mới embed mỗi 30 giây
    và gửi lại mỗi 5 phút để giữ embed luôn hiển thị ở cuối kênh.
─────────────────────────────────────────────────────────────────────────────
"""

import discord
import wavelink
import asyncio
from discord import Embed, Colour
from utils.helpers import format_duration, progress_bar, get_loop_status


# ─── Embed Builder ────────────────────────────────────────────────────────

def build_nowplaying_embed(player: wavelink.Player, track: wavelink.Playable) -> Embed:
    """
    EN: Construct the "Now Playing" embed for the given player and track.
        Colour and source icon adapt dynamically based on the track's URI.
    VI: Tạo embed "Đang phát" cho player và bài nhạc đã cho.
        Màu sắc và icon nguồn tự động thay đổi dựa trên URI của bài nhạc.
    """
    uri = getattr(track, 'uri', '') or ''

    # EN: Detect platform from URI for consistent colour coding.
    # VI: Phát hiện nền tảng từ URI để tô màu nhất quán.
    if 'spotify' in uri:
        source_icon, source_color = "🎵 Spotify", Colour.green()
    elif 'soundcloud' in uri:
        source_icon, source_color = "🔊 SoundCloud", Colour.orange()
    else:
        source_icon, source_color = "▶️ YouTube", Colour.red()

    embed = Embed(
        title="🎵 Đang phát",
        description=f"**[{track.title[:70]}]({uri})**\n👤 {track.author} • {source_icon}",
        color=source_color
    )

    # EN: Progress bar — only shown for finite-length tracks (not live streams).
    # VI: Thanh tiến trình — chỉ hiện cho bài có thời lượng xác định (không phải livestream).
    length = getattr(track, 'length', 0) or 0
    pos = player.position or 0
    if length:
        bar = progress_bar(pos, length)
        embed.add_field(
            name="⏱ Tiến trình",
            value=f"`{format_duration(pos)}` [{bar}] `{format_duration(length)}`",
            inline=False
        )

    # EN: Status fields — queue size, loop mode, volume.
    # VI: Các trường trạng thái — số bài trong queue, chế độ lặp, âm lượng.
    embed.add_field(name="📋 Queue",   value=f"{player.queue.count} bài tiếp",      inline=True)
    embed.add_field(name="🔁 Chế độ", value=get_loop_status(player.queue.mode),     inline=True)
    embed.add_field(name="🔊 Volume",  value=f"{player.volume}%",                   inline=True)

    # EN: Thumbnail from track artwork if available (YouTube/Spotify provide this).
    # VI: Ảnh thu nhỏ từ artwork của bài nếu có (YouTube/Spotify cung cấp).
    thumb = getattr(track, 'artwork', None)
    if thumb:
        embed.set_thumbnail(url=thumb)

    embed.set_footer(text="Tự động cập nhật mỗi 30 giây")
    return embed


# ─── Interactive Button View ──────────────────────────────────────────────

class NowPlayingView(discord.ui.View):
    """
    EN: Persistent button row attached to the Now Playing embed.
        Buttons: Stop | Skip | Pause/Resume | Loop cycle.
        timeout=None keeps buttons active indefinitely (until the bot restarts).
    VI: Hàng nút tương tác gắn vào embed Now Playing.
        Các nút: Dừng | Bỏ qua | Tạm dừng/Tiếp tục | Chuyển chế độ lặp.
        timeout=None giữ nút hoạt động vô thời hạn (đến khi bot khởi động lại).
    """

    def __init__(self, player: wavelink.Player):
        super().__init__(timeout=None)
        self.player = player
        self._sync_loop_button()  # EN: set initial label/style / VI: đặt nhãn/kiểu ban đầu

    def _sync_loop_button(self):
        """
        EN: Update the Loop button's label and colour to reflect the current mode.
            Called on init and after each loop state change.
        VI: Cập nhật nhãn và màu nút Loop theo chế độ hiện tại.
            Gọi khi khởi tạo và sau mỗi lần đổi chế độ lặp.
        """
        btn = self.loop_btn
        if self.player.queue.mode == wavelink.QueueMode.loop:
            btn.label = "🔂 Loop: Bài"
            btn.style = discord.ButtonStyle.success
        elif self.player.queue.mode == wavelink.QueueMode.loop_all:
            btn.label = "🔁 Loop: Tất cả"
            btn.style = discord.ButtonStyle.primary
        else:
            btn.label = "🔁 Loop: Tắt"
            btn.style = discord.ButtonStyle.secondary

    # ── Stop ──────────────────────────────────────────────────────────────
    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.danger, row=0)
    async def stop_btn(self, interaction: discord.Interaction, _):
        """
        EN: Clear the queue, stop playback, and disconnect the bot from voice.
        VI: Xóa queue, dừng phát nhạc, và ngắt kết nối bot khỏi voice.
        """
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message("❌ Bot chưa vào voice!", ephemeral=True)
        player.queue.clear()
        await player.stop()
        await player.disconnect()
        embed = Embed(title="⏹ Đã dừng", description="Bot đã rời voice channel.", color=Colour.red())
        # EN: Replace embed + remove buttons after stopping.
        # VI: Thay embed + xóa nút sau khi dừng.
        await interaction.response.edit_message(embed=embed, view=None)

    # ── Skip ──────────────────────────────────────────────────────────────
    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.blurple, row=0)
    async def skip_btn(self, interaction: discord.Interaction, _):
        """
        EN: Skip the current track. wavelink will automatically fire
            on_wavelink_track_end, which plays the next queued track.
        VI: Bỏ qua bài hiện tại. wavelink tự động kích hoạt
            on_wavelink_track_end, sẽ phát bài tiếp theo trong queue.
        """
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.playing:
            return await interaction.response.send_message("❌ Không có bài đang phát!", ephemeral=True)
        await player.skip()
        # EN: ephemeral=True → only the clicker sees the confirmation.
        # VI: ephemeral=True → chỉ người bấm mới thấy xác nhận.
        await interaction.response.send_message("⏭ Đã skip!", ephemeral=True)

    # ── Pause / Resume ────────────────────────────────────────────────────
    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.grey, row=0)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        EN: Toggle pause state. The button label flips between Pause and Resume
            and the button colour changes to give clear visual feedback.
        VI: Chuyển đổi trạng thái tạm dừng. Nhãn nút đổi giữa Pause và Resume,
            màu nút thay đổi để phản hồi trực quan rõ ràng.
        """
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message("❌ Bot chưa vào voice!", ephemeral=True)
        await player.pause(not player.paused)
        button.label = "▶️ Resume" if player.paused else "⏸ Pause"
        button.style = discord.ButtonStyle.success if player.paused else discord.ButtonStyle.grey
        await interaction.response.edit_message(view=self)

    # ── Loop Cycle ────────────────────────────────────────────────────────
    @discord.ui.button(label="🔁 Loop: Tắt", style=discord.ButtonStyle.secondary, row=0)
    async def loop_btn(self, interaction: discord.Interaction, _):
        """
        EN: Cycle through loop modes: Normal → Loop Track → Loop All → Normal.
        VI: Xoay vòng qua các chế độ lặp: Thường → Lặp bài → Lặp tất cả → Thường.
        """
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message("❌ Bot chưa vào voice!", ephemeral=True)
        if player.queue.mode == wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.loop
        elif player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.loop_all
        else:
            player.queue.mode = wavelink.QueueMode.normal
        self._sync_loop_button()
        await interaction.response.edit_message(view=self)


# ─── Now Playing Manager ──────────────────────────────────────────────────

class NowPlayingManager:
    """
    EN: Singleton-style manager (one instance per bot process) that tracks
        the Now Playing message for every active guild and runs a background
        refresh loop to keep it up to date.

        Key design decisions:
        • Send new message BEFORE deleting the old one, so there is never
          a gap where no message exists.
        • Re-send every 5 minutes so the embed stays near the bottom of chat.
        • Edit every 30 seconds in between to show live progress.

    VI: Manager kiểu singleton (một instance cho toàn bộ tiến trình bot)
        theo dõi message Now Playing cho từng guild đang hoạt động và chạy
        vòng lặp nền để cập nhật.

        Quyết định thiết kế chính:
        • Gửi message MỚI TRƯỚC khi xóa cái cũ, tránh khoảng trống không có message.
        • Gửi lại mỗi 5 phút để embed luôn ở cuối kênh chat.
        • Edit mỗi 30 giây ở giữa để hiển thị tiến trình trực tiếp.
    """

    def __init__(self):
        # EN: guild_id → discord.Message (the current Now Playing message)
        # VI: guild_id → discord.Message (message Now Playing hiện tại)
        self.messages: dict[int, discord.Message] = {}

        # EN: guild_id → discord.TextChannel (where to send/re-send)
        # VI: guild_id → discord.TextChannel (kênh để gửi/gửi lại)
        self.channels: dict[int, discord.TextChannel] = {}

        # EN: guild_id → asyncio.Task (the background refresh coroutine)
        # VI: guild_id → asyncio.Task (coroutine làm mới nền)
        self.tasks: dict[int, asyncio.Task] = {}

    # ── Public: send first message ────────────────────────────────────────
    async def send(self, source, player: wavelink.Player, track: wavelink.Playable):
        """
        EN: Send the initial Now Playing message when a track starts.
            Accepts either a commands.Context or a discord.Interaction
            so it can be called from both prefix commands and slash commands.
        VI: Gửi message Now Playing lần đầu khi bắt đầu phát bài.
            Chấp nhận cả commands.Context lẫn discord.Interaction
            để có thể gọi từ cả prefix command và slash command.
        """
        embed = build_nowplaying_embed(player, track)
        view  = NowPlayingView(player)

        # EN: Unify guild_id / channel extraction regardless of source type.
        # VI: Lấy guild_id / channel thống nhất bất kể kiểu source.
        guild_id = source.guild.id
        channel  = source.channel

        try:
            msg = await channel.send(embed=embed, view=view)
            self.messages[guild_id] = msg
            self.channels[guild_id] = channel
            self._start_task(guild_id, player)  # EN: start refresh loop / VI: khởi động vòng làm mới
        except discord.HTTPException as e:
            print(f"❌ NowPlaying send failed: {e}")

    # ── Public: update when track changes ────────────────────────────────
    async def update(self, guild_id: int, player: wavelink.Player, track: wavelink.Playable):
        """
        EN: Called by the track_start event when the next track begins.
            Re-sends the embed with the new track's information.
        VI: Được gọi bởi sự kiện track_start khi bài tiếp theo bắt đầu.
            Gửi lại embed với thông tin bài mới.
        """
        await self._resend(guild_id, player, track)

    # ── Internal: safe delete ─────────────────────────────────────────────
    async def _safe_delete(self, msg: discord.Message):
        """
        EN: Delete a message while silently swallowing common errors
            (already deleted, missing permissions, API error).
        VI: Xóa message trong khi im lặng bỏ qua các lỗi phổ biến
            (đã bị xóa, thiếu quyền, lỗi API).
        """
        try:
            await msg.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    # ── Internal: send-new-then-delete-old ───────────────────────────────
    async def _resend(self, guild_id: int, player: wavelink.Player, track: wavelink.Playable = None):
        """
        EN: Core re-send logic:
            1. Send brand-new message (guarantees continuity even if send fails).
            2. Only after success, delete the previous message.
        VI: Logic gửi lại cốt lõi:
            1. Gửi message hoàn toàn mới (đảm bảo liên tục ngay cả khi gửi thất bại).
            2. Chỉ sau khi thành công, xóa message trước đó.
        """
        channel = self.channels.get(guild_id)
        if not channel:
            return

        current = track or player.current
        if not current:
            return

        embed = build_nowplaying_embed(player, current)
        view  = NowPlayingView(player)

        try:
            new_msg = await channel.send(embed=embed, view=view)
        except discord.HTTPException as e:
            # EN: If send fails, keep the old message intact — don't delete it.
            # VI: Nếu gửi thất bại, giữ nguyên message cũ — không xóa.
            print(f"❌ NowPlaying resend failed: {e}")
            return

        old_msg = self.messages.get(guild_id)
        self.messages[guild_id] = new_msg  # EN: register new message first / VI: đăng ký message mới trước

        if old_msg:
            await self._safe_delete(old_msg)

    # ── Internal: background refresh task ────────────────────────────────
    def _start_task(self, guild_id: int, player: wavelink.Player):
        """
        EN: Spawn (or replace) the per-guild background task that:
              • Every 30 s  → edit the existing message (live progress update)
              • Every 5 min → re-send a fresh message (stays at chat bottom)
            The task exits automatically when the player stops.
        VI: Tạo (hoặc thay thế) tác vụ nền theo guild:
              • Mỗi 30 giây → edit message hiện có (cập nhật tiến trình trực tiếp)
              • Mỗi 5 phút  → gửi lại message mới (luôn nằm cuối kênh chat)
            Tác vụ tự thoát khi player dừng.
        """
        # EN: Cancel any existing task for this guild before starting a new one.
        # VI: Hủy tác vụ hiện có của guild này trước khi tạo cái mới.
        if guild_id in self.tasks:
            self.tasks[guild_id].cancel()

        async def _loop():
            tick = 0
            while True:
                await asyncio.sleep(30)  # EN: wait 30 s between ticks / VI: chờ 30 giây giữa mỗi tick

                # EN: Exit loop if nothing is playing anymore.
                # VI: Thoát vòng lặp nếu không còn gì đang phát.
                if not player.playing or not player.current:
                    break

                tick += 1

                # EN: Every 10 ticks (5 minutes) — re-send to keep embed visible.
                # VI: Mỗi 10 tick (5 phút) — gửi lại để giữ embed hiển thị.
                if tick % 10 == 0:
                    await self._resend(guild_id, player)
                    continue

                msg = self.messages.get(guild_id)

                if not msg:
                    # EN: Message was deleted externally — re-send rather than edit.
                    # VI: Message bị xóa bên ngoài — gửi lại thay vì edit.
                    await self._resend(guild_id, player)
                    continue

                try:
                    embed = build_nowplaying_embed(player, player.current)
                    view  = NowPlayingView(player)
                    await msg.edit(embed=embed, view=view)
                except discord.NotFound:
                    # EN: Message no longer exists on Discord side.
                    # VI: Message không còn tồn tại phía Discord.
                    self.messages.pop(guild_id, None)
                    await self._resend(guild_id, player)
                except discord.HTTPException:
                    # EN: Unrecoverable API error — break to avoid spam.
                    # VI: Lỗi API không thể khôi phục — break để tránh spam.
                    break

        self.tasks[guild_id] = asyncio.create_task(_loop())

    # ── Public: stop and clean up ─────────────────────────────────────────
    async def stop(self, guild_id: int):
        """
        EN: Called when the queue is exhausted or the bot disconnects.
            Cancels the refresh task and deletes the Now Playing message.
        VI: Được gọi khi hết queue hoặc bot ngắt kết nối.
            Hủy tác vụ làm mới và xóa message Now Playing.
        """
        if guild_id in self.tasks:
            self.tasks[guild_id].cancel()
            del self.tasks[guild_id]

        msg = self.messages.pop(guild_id, None)
        if msg:
            await self._safe_delete(msg)

        self.channels.pop(guild_id, None)
