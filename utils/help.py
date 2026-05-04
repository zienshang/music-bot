"""
utils/help.py
─────────────────────────────────────────────────────────────────────────────
EN: Custom HelpCommand that replaces discord.py's built-in help with
    polished Discord embeds showing per-command details and aliases.
VI: HelpCommand tùy chỉnh thay thế help mặc định của discord.py bằng
    Discord embed đẹp, hiển thị chi tiết từng lệnh và alias.
─────────────────────────────────────────────────────────────────────────────
"""

import discord
from discord.ext import commands
import config

# ─── Command Metadata Registry ────────────────────────────────────────────
# EN: Static lookup table mapping command name → (icon, description, usage).
#     Centralising this here means only one place needs updating when a
#     command is renamed or its syntax changes.
# VI: Bảng tra cứu tĩnh ánh xạ tên lệnh → (icon, mô tả, cú pháp dùng).
#     Tập trung ở đây nghĩa là chỉ cần cập nhật một chỗ khi đổi tên lệnh
#     hoặc thay đổi cú pháp.
COMMAND_INFO = {
    "play":     ("🎵", "Phát nhạc từ YouTube, Spotify, SoundCloud", "-play <tên bài hoặc link>"),
    "addtrack": ("➕", "Thêm bài vào queue (không phát ngay)",      "-addtrack <tên bài hoặc link>"),
    "skip":     ("⏭", "Bỏ qua bài đang phát",                      "-skip"),
    "queue":    ("📋", "Xem danh sách phát",                        "-queue"),
    "shuffle":  ("🔀", "Trộn ngẫu nhiên queue",                     "-shuffle"),
    "loop":     ("🔁", "Bật/tắt loop (Tắt → Bài → Tất cả)",        "-loop"),
    "volume":   ("🔊", "Chỉnh âm lượng (0–1000)",                   "-volume <số>"),
    "leave":    ("👋", "Bot rời voice channel",                     "-leave"),
    "clear":    ("🗑️", "Xóa toàn bộ queue",                        "-clear"),
}


class MyHelp(commands.HelpCommand):
    """
    EN: Subclass of HelpCommand that sends embedded messages instead of
        plain text. Three display modes:
          • send_bot_help     → -help (all commands)
          • send_command_help → -help <command>
          • send_cog_help     → -help <CogName>
    VI: Subclass của HelpCommand gửi embedded message thay vì văn bản thường.
        Ba chế độ hiển thị:
          • send_bot_help     → -help (tất cả lệnh)
          • send_command_help → -help <lệnh>
          • send_cog_help     → -help <TênCog>
    """

    def __init__(self):
        super().__init__(
            # EN: Register -help itself as a command with alias -h.
            # VI: Đăng ký -help như một lệnh với alias -h.
            command_attrs={"aliases": ["h"], "help": "Hiển thị danh sách lệnh"},
            verify_checks=False  # EN: show hidden/owner-only commands too / VI: hiện cả lệnh ẩn/owner
        )

    # ──────────────────────────────────────────────────────────────────────
    async def send_bot_help(self, mapping):
        """
        EN: Invoked when the user types "-help" with no arguments.
            Shows all registered commands in a single embed.
        VI: Được gọi khi người dùng gõ "-help" không có tham số.
            Hiển thị tất cả lệnh đã đăng ký trong một embed.
        """
        embed = discord.Embed(
            title="🎵 Music Bot — Danh sách lệnh",
            description=(
                "Bot nhạc hỗ trợ **YouTube**, **Spotify**, **SoundCloud**\n"
                f"Dùng `{config.PREFIX}help <lệnh>` để xem chi tiết từng lệnh\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x00ffcc
        )

        # EN: Build a formatted block listing every command with icon + usage.
        # VI: Xây dựng khối văn bản liệt kê từng lệnh với icon + cú pháp.
        music_cmds = ""
        for name, (icon, desc, usage) in COMMAND_INFO.items():
            music_cmds += f"{icon} **`{usage}`**\n┗ {desc}\n"

        embed.add_field(name="🎧 Lệnh nhạc", value=music_cmds, inline=False)
        embed.set_thumbnail(url=self.context.bot.user.display_avatar.url)
        embed.set_footer(
            text="Made with ❤️ by exec77.sh  •  Prefix: -",
            icon_url=self.context.bot.user.display_avatar.url
        )
        await self.get_destination().send(embed=embed)

    # ──────────────────────────────────────────────────────────────────────
    async def send_command_help(self, command):
        """
        EN: Invoked when the user types "-help <command_name>".
            Shows description, usage syntax, and any registered aliases.
        VI: Được gọi khi người dùng gõ "-help <tên_lệnh>".
            Hiển thị mô tả, cú pháp dùng và các alias đã đăng ký.
        """
        # EN: Fall back to generic info if this command isn't in COMMAND_INFO.
        # VI: Dùng thông tin chung nếu lệnh không có trong COMMAND_INFO.
        info = COMMAND_INFO.get(command.name)
        icon, desc, usage = info if info else ("⚙️", command.help or "Không có mô tả", f"-{command.name}")

        embed = discord.Embed(title=f"{icon} Lệnh: `{command.name}`", color=0x00ffcc)
        embed.add_field(name="📌 Mô tả",  value=desc,           inline=False)
        embed.add_field(name="🔧 Cú pháp", value=f"`{usage}`",  inline=False)

        if command.aliases:
            # EN: Display all aliases so users know shortcut forms (e.g. -p, -pl).
            # VI: Hiển thị tất cả alias để người dùng biết dạng tắt (vd: -p, -pl).
            aliases = " ".join(f"`{a}`" for a in command.aliases)
            embed.add_field(name="🔗 Alias", value=aliases, inline=False)

        embed.set_footer(
            text="Made with ❤️ by exec77.sh  •  Prefix: -",
            icon_url=self.context.bot.user.display_avatar.url
        )
        await self.get_destination().send(embed=embed)

    # ──────────────────────────────────────────────────────────────────────
    async def send_cog_help(self, cog):
        """
        EN: Invoked when the user types "-help <CogName>".
            Lists all non-hidden commands belonging to that Cog.
        VI: Được gọi khi người dùng gõ "-help <TênCog>".
            Liệt kê tất cả lệnh không ẩn thuộc Cog đó.
        """
        embed = discord.Embed(title=f"📁 {cog.qualified_name}", color=0x5865F2)

        for cmd in cog.get_commands():
            if not cmd.hidden:
                info = COMMAND_INFO.get(cmd.name)
                icon, desc, usage = info if info else ("⚙️", cmd.help or "Không có mô tả", f"-{cmd.name}")
                embed.add_field(name=f"{icon} `{usage}`", value=desc, inline=False)

        embed.set_footer(
            text="Made with ❤️ by exec77.sh  •  Prefix: -",
            icon_url=self.context.bot.user.display_avatar.url
        )
        await self.get_destination().send(embed=embed)

    # ──────────────────────────────────────────────────────────────────────
    async def send_error_message(self, error):
        """
        EN: Called when the help system can't find the requested command/cog.
            Sends a red error embed instead of a raw exception.
        VI: Được gọi khi hệ thống help không tìm thấy lệnh/cog yêu cầu.
            Gửi embed lỗi màu đỏ thay vì exception thô.
        """
        embed = discord.Embed(
            title="❌ Không tìm thấy lệnh",
            description=f"{error}\nDùng `{config.PREFIX}help` để xem danh sách lệnh.",
            color=0xff4444
        )
        await self.get_destination().send(embed=embed)
