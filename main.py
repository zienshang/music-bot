"""
main.py
─────────────────────────────────────────────────────────────────────────────
EN: Bot entry point. Creates the Discord client, loads all Cogs (feature
    modules), connects to the Lavalink audio node, then starts the bot.
VI: Điểm khởi động của bot. Tạo Discord client, nạp tất cả Cog (module
    tính năng), kết nối Lavalink audio node, sau đó khởi chạy bot.
─────────────────────────────────────────────────────────────────────────────
"""

import discord
from discord.ext import commands
import config
import wavelink
from utils.help import MyHelp  # EN: custom help command / VI: lệnh help tùy chỉnh

# ─── Intents ──────────────────────────────────────────────────────────────
# EN: Intents declare which Gateway events Discord should send to the bot.
#     message_content → needed to read prefix commands
#     voice_states    → needed to track who joins/leaves voice channels
# VI: Intents khai báo sự kiện Gateway nào Discord sẽ gửi cho bot.
#     message_content → cần để đọc prefix command
#     voice_states    → cần để theo dõi ai vào/rời voice channel
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# ─── Bot Instance ─────────────────────────────────────────────────────────
# EN: The main Bot object. Uses the prefix and custom help command defined
#     in config.py and help.py respectively.
# VI: Object Bot chính. Dùng prefix và lệnh help tùy chỉnh được định nghĩa
#     trong config.py và help.py.
bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=MyHelp()
)

# ─── Cog Registry ─────────────────────────────────────────────────────────
# EN: List of all extension (Cog) module paths to load on startup.
#     Each string maps to a Python file: "cogs.music.play" → cogs/music/play.py
# VI: Danh sách đường dẫn module extension (Cog) cần nạp khi khởi động.
#     Mỗi chuỗi trỏ đến file Python: "cogs.music.play" → cogs/music/play.py
COGS = [
    "utils.status",         # EN: bot presence / VI: trạng thái bot
    "cogs.music.play",      # EN: main play command / VI: lệnh phát nhạc chính
    "cogs.music.addtrack",  # EN: queue a track without playing / VI: thêm bài vào queue
    "cogs.music.skip",      # EN: skip current track / VI: bỏ qua bài đang phát
    "cogs.music.queue",     # EN: display queue / VI: hiển thị danh sách phát
    "cogs.music.shuffle",   # EN: shuffle queue / VI: trộn ngẫu nhiên queue
    "cogs.music.loop",      # EN: toggle loop mode / VI: bật/tắt chế độ lặp
    "cogs.music.volume",    # EN: adjust volume / VI: chỉnh âm lượng
    "cogs.music.leave",     # EN: disconnect bot / VI: ngắt kết nối bot
    "cogs.music.clear_queue",  # EN: clear queue / VI: xóa toàn bộ queue
]


@bot.event
async def setup_hook():
    """
    EN: Called once before the bot logs in. Used to load Cogs and connect
        to the Lavalink node asynchronously.
    VI: Được gọi một lần trước khi bot đăng nhập. Dùng để nạp Cog và
        kết nối Lavalink node một cách bất đồng bộ.
    """
    # EN: Load each Cog; print result so startup errors are visible in logs.
    # VI: Nạp từng Cog; in kết quả để lỗi khởi động hiện rõ trong log.
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed {cog}: {e}")

    # EN: Create a Lavalink node and register it with wavelink's pool.
    #     The pool manages multiple nodes; here we use a single local node.
    # VI: Tạo Lavalink node và đăng ký vào pool của wavelink.
    #     Pool quản lý nhiều node; ở đây dùng một node local duy nhất.
    node = wavelink.Node(uri=config.LAVALINK_URI, password=config.LAVALINK_PASSWORD)
    await wavelink.Pool.connect(nodes=[node], client=bot)
    print("🔥 Lavalink connected!")


@bot.event
async def on_ready():
    """
    EN: Fired when the bot has successfully connected to Discord and is
        ready to receive events. Prints a summary of joined guilds.
    VI: Kích hoạt khi bot kết nối Discord thành công và sẵn sàng nhận sự kiện.
        In ra danh sách server đang tham gia.
    """
    print(f"🤖 Bot ready: {bot.user}")
    print(f"📊 Đang có mặt trong {len(bot.guilds)} server(s):")
    for i, guild in enumerate(bot.guilds, 1):
        print(f"  {i}. {guild.name} (ID: {guild.id}) - {len(guild.members)} members")


@bot.event
async def on_wavelink_node_ready(payload):
    """
    EN: Fired when a Lavalink node successfully connects and is ready.
    VI: Kích hoạt khi Lavalink node kết nối thành công và sẵn sàng hoạt động.
    """
    print(f"🎵 Node ready: {payload.node.identifier}")


@bot.event
async def on_wavelink_node_error(node: wavelink.Node, error: Exception):
    """
    EN: Fired when a Lavalink node encounters an error. Logs the error
        so it can be investigated without crashing the bot.
    VI: Kích hoạt khi Lavalink node gặp lỗi. Ghi log để điều tra
        mà không làm crash bot.
    """
    print(f"❌ Node error: {error}")


@bot.event
async def on_command_error(ctx, error):
    """
    EN: Global error handler. Silently ignores unknown commands so the bot
        doesn't spam error messages for typos. All other errors are re-raised
        so Cog-level handlers or the default handler can process them.
    VI: Bộ xử lý lỗi toàn cục. Im lặng bỏ qua lệnh không tồn tại để bot
        không spam thông báo lỗi khi người dùng gõ sai. Các lỗi khác
        được re-raise để Cog hoặc handler mặc định xử lý tiếp.
    """
    if isinstance(error, commands.CommandNotFound):
        return  # EN: ignore silently / VI: bỏ qua im lặng
    raise error


# ─── Start Bot ────────────────────────────────────────────────────────────
# EN: Blocking call that opens the Discord WebSocket connection and runs
#     the event loop until the process is killed.
# VI: Lời gọi blocking mở kết nối WebSocket Discord và chạy event loop
#     cho đến khi tiến trình bị dừng.
bot.run(config.TOKEN)
