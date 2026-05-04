"""
utils/status.py
─────────────────────────────────────────────────────────────────────────────
EN: StatusManager Cog. Handles two kinds of status updates:
      1. Bot presence (activity shown under the bot's name in Discord).
      2. Voice channel status (the text label visible on the channel tile).
    Both update automatically in response to wavelink playback events.
VI: Cog StatusManager. Xử lý hai loại cập nhật trạng thái:
      1. Presence của bot (hoạt động hiển thị dưới tên bot trong Discord).
      2. Trạng thái voice channel (nhãn văn bản hiển thị trên ô kênh).
    Cả hai tự động cập nhật theo sự kiện phát nhạc của wavelink.
─────────────────────────────────────────────────────────────────────────────
"""

import discord
import asyncio
import wavelink
from discord.ext import commands, tasks

# ─── Idle Status Rotation ─────────────────────────────────────────────────
# EN: Shown when the bot is not playing music in any server.
#     Cycles through these entries every 30 seconds via _status_loop.
# VI: Hiển thị khi bot không phát nhạc ở bất kỳ server nào.
#     Xoay vòng qua các mục này mỗi 30 giây qua _status_loop.
IDLE_STATUSES = [
    (discord.ActivityType.listening, "🎵 -play để phát nhạc"),
    (discord.ActivityType.watching,  "YouTube | Spotify | SoundCloud"),
    (discord.ActivityType.playing,   "Music Bot 🎧"),
    (discord.ActivityType.listening, "-help để xem lệnh"),
    (discord.ActivityType.watching,  "queue của bạn 📋"),
]


class StatusManager(commands.Cog):
    """
    EN: Cog that keeps the bot's presence and voice-channel status in sync
        with what's actually playing. Uses a tasks.loop for idle rotation
        and wavelink event listeners for real-time updates.
    VI: Cog giữ presence và trạng thái voice channel của bot đồng bộ
        với những gì đang thực sự phát. Dùng tasks.loop để xoay vòng khi idle
        và event listener của wavelink để cập nhật thời gian thực.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._idle_index = 0      # EN: pointer into IDLE_STATUSES / VI: con trỏ vào IDLE_STATUSES
        self._status_loop.start() # EN: begin the 30-second rotation / VI: bắt đầu xoay vòng 30 giây

    def cog_unload(self):
        """
        EN: Called by discord.py when the Cog is removed. Stops the loop
            to prevent asyncio errors after the bot shuts down.
        VI: Được gọi bởi discord.py khi Cog bị gỡ. Dừng vòng lặp
            để tránh lỗi asyncio sau khi bot tắt.
        """
        self._status_loop.cancel()

    # ──────────────────────────────────────────────────────────────────────
    def _active_players(self) -> int:
        """
        EN: Count how many guilds currently have an active (playing) voice client.
        VI: Đếm số guild hiện đang có voice client đang phát nhạc.
        """
        return sum(
            1 for guild in self.bot.guilds
            if guild.voice_client and guild.voice_client.playing
        )

    # ──────────────────────────────────────────────────────────────────────
    async def _update_bot_status(self):
        """
        EN: Set the bot's Discord presence.
            • Playing in 1+ servers → "online" + "Listening to … 🎵"
            • Idle                  → rotate through IDLE_STATUSES (idle status)
        VI: Đặt presence Discord của bot.
            • Đang phát ở 1+ server → "online" + "Listening to … 🎵"
            • Không hoạt động       → xoay vòng qua IDLE_STATUSES (trạng thái idle)
        """
        active = self._active_players()

        if active > 0:
            label = f"nhạc trên {active} server 🎵" if active > 1 else "Playing Music 🎵"
            activity = discord.Activity(type=discord.ActivityType.listening, name=label)
            status   = discord.Status.online
        else:
            atype, name = IDLE_STATUSES[self._idle_index % len(IDLE_STATUSES)]
            activity     = discord.Activity(type=atype, name=name)
            status       = discord.Status.idle
            self._idle_index += 1  # EN: advance to next idle status / VI: tiến đến trạng thái idle tiếp theo

        await self.bot.change_presence(status=status, activity=activity)

    # ──────────────────────────────────────────────────────────────────────
    async def _set_voice_status(self, guild: discord.Guild, text: str):
        """
        EN: Set the visible status text on the voice channel the bot occupies.
            Only VoiceChannel supports this — StageChannel does not.
            Silently ignores permission / API errors so music keeps playing.
        VI: Đặt văn bản trạng thái hiển thị trên voice channel bot đang ở.
            Chỉ VoiceChannel hỗ trợ — StageChannel thì không.
            Im lặng bỏ qua lỗi quyền / API để nhạc tiếp tục phát.
        """
        player: wavelink.Player = guild.voice_client
        if not player or not player.channel:
            return
        try:
            if isinstance(player.channel, discord.VoiceChannel):
                await player.channel.edit(status=text)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"⚠️ Không thể đặt voice status: {e}")

    async def _clear_voice_status(self, guild: discord.Guild):
        """
        EN: Convenience wrapper — removes the voice channel status (set to None).
        VI: Wrapper tiện lợi — xóa trạng thái voice channel (đặt thành None).
        """
        await self._set_voice_status(guild, None)

    # ─── 30-second bot presence loop ──────────────────────────────────────
    @tasks.loop(seconds=30)
    async def _status_loop(self):
        """
        EN: Periodically refresh the bot's presence so idle statuses rotate
            and the active-player count stays accurate.
        VI: Định kỳ làm mới presence của bot để trạng thái idle xoay vòng
            và số lượng player đang hoạt động luôn chính xác.
        """
        await self._update_bot_status()

    @_status_loop.before_loop
    async def _before_loop(self):
        """
        EN: Wait until the bot is fully connected before starting the loop,
            otherwise change_presence will fail.
        VI: Đợi bot kết nối hoàn toàn trước khi bắt đầu vòng lặp,
            nếu không change_presence sẽ thất bại.
        """
        await self.bot.wait_until_ready()

    # ─── wavelink event listeners ─────────────────────────────────────────

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """
        EN: Fired when a new track begins playing.
            Updates the voice channel status with the track title and
            refreshes the bot presence to show it is actively playing.
        VI: Kích hoạt khi bài nhạc mới bắt đầu phát.
            Cập nhật trạng thái voice channel với tên bài và
            làm mới presence bot để hiển thị đang phát nhạc.
        """
        player = payload.player
        track  = payload.track
        if not player or not player.guild:
            return

        # EN: Truncate long titles so they fit in the channel status field.
        # VI: Cắt ngắn tiêu đề dài để vừa với trường trạng thái kênh.
        title = track.title[:40]
        await self._set_voice_status(player.guild, f"🎵 {title}")
        await self._update_bot_status()

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """
        EN: Fired when a track finishes (naturally or via skip).
            Waits 1 s for the queue to process the next track, then
            clears the voice status if nothing new is playing.
        VI: Kích hoạt khi bài nhạc kết thúc (tự nhiên hoặc do skip).
            Chờ 1 giây để queue xử lý bài tiếp theo, sau đó
            xóa trạng thái voice nếu không có gì đang phát.
        """
        player = payload.player
        if not player or not player.guild:
            return

        await asyncio.sleep(1)  # EN: allow queue to start next track / VI: cho queue bắt đầu bài tiếp theo

        if player.queue.is_empty and not player.playing:
            await self._clear_voice_status(player.guild)

        await self._update_bot_status()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState):
        """
        EN: Fired on any voice state change across the guild.
            We filter to only act when the bot itself leaves a channel,
            then clear the channel's status text so it doesn't persist.
        VI: Kích hoạt khi bất kỳ trạng thái voice nào thay đổi trong guild.
            Lọc chỉ xử lý khi chính bot rời kênh,
            sau đó xóa văn bản trạng thái kênh để không còn hiển thị.
        """
        if member != member.guild.me:
            return  # EN: ignore state changes from other members / VI: bỏ qua thay đổi từ thành viên khác

        # EN: Bot left a channel (had one before, has none after).
        # VI: Bot vừa rời kênh (trước có kênh, sau không có).
        if before.channel and not after.channel:
            try:
                if isinstance(before.channel, discord.VoiceChannel):
                    await before.channel.edit(status=None)
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusManager(bot))
