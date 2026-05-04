"""
utils/helpers.py
─────────────────────────────────────────────────────────────────────────────
EN: Shared utility functions used across multiple Cogs.
    Keeps formatting and detection logic in one place (DRY principle).
VI: Các hàm tiện ích dùng chung cho nhiều Cog.
    Tập trung logic định dạng và phát hiện nguồn vào một chỗ (nguyên tắc DRY).
─────────────────────────────────────────────────────────────────────────────
"""

import wavelink
from discord import Colour


def get_source(search: str) -> tuple[str, Colour]:
    """
    EN: Detect the audio source from a query string or URL and return a
        matching icon label and embed colour for consistent UI styling.
        Priority: Spotify > SoundCloud > YouTube (default).
    VI: Phát hiện nguồn âm thanh từ chuỗi tìm kiếm hoặc URL và trả về
        nhãn icon + màu embed tương ứng để giao diện nhất quán.
        Ưu tiên: Spotify > SoundCloud > YouTube (mặc định).

    Args:
        search: EN: Raw query or URL typed by the user.
                VI: Chuỗi tìm kiếm hoặc URL người dùng nhập.

    Returns:
        EN: Tuple of (icon_string, discord.Colour).
        VI: Tuple gồm (chuỗi icon, discord.Colour).
    """
    if any(x in search for x in ("spotify.com", "open.spotify", "spsearch:")):
        return "🎵 Spotify", Colour.green()
    elif any(x in search for x in ("soundcloud.com", "scsearch:")):
        return "🔊 SoundCloud", Colour.orange()
    else:
        # EN: Default to YouTube for plain keywords or youtube.com links.
        # VI: Mặc định là YouTube cho từ khóa thường hoặc link youtube.com.
        return "▶️ YouTube", Colour.red()


def format_duration(ms: int) -> str:
    """
    EN: Convert a duration in milliseconds to a human-readable string.
        Output format: "m:ss" or "h:mm:ss" for tracks over an hour.
    VI: Chuyển đổi thời lượng từ mili-giây sang chuỗi dễ đọc.
        Định dạng: "m:ss" hoặc "h:mm:ss" cho bài dài hơn một tiếng.

    Args:
        ms: EN: Duration in milliseconds (as returned by wavelink).
            VI: Thời lượng tính bằng mili-giây (như wavelink trả về).

    Returns:
        EN: Formatted time string, or "00:00" for invalid input.
        VI: Chuỗi thời gian đã định dạng, hoặc "00:00" nếu đầu vào không hợp lệ.
    """
    if not ms or ms <= 0:
        return "00:00"

    # EN: Strip milliseconds, then split into minutes/seconds and hours/minutes.
    # VI: Bỏ mili-giây, sau đó tách thành phút/giây và giờ/phút.
    m, s = divmod(ms // 1000, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def progress_bar(position: int, length: int, size: int = 20) -> str:
    """
    EN: Build a text-based progress bar using block characters.
        Filled portion uses "▓", empty portion uses "░".
    VI: Tạo thanh tiến trình dạng văn bản bằng ký tự khối.
        Phần đã phát dùng "▓", phần còn lại dùng "░".

    Args:
        position: EN: Current playback position in ms.
                  VI: Vị trí phát hiện tại tính bằng ms.
        length:   EN: Total track length in ms.
                  VI: Tổng thời lượng bài tính bằng ms.
        size:     EN: Number of characters wide the bar should be (default 20).
                  VI: Số ký tự chiều rộng thanh bar (mặc định 20).

    Returns:
        EN: A string of exactly `size` characters.
        VI: Chuỗi có đúng `size` ký tự.
    """
    if not length:
        # EN: Guard against division by zero for streams or unknown length.
        # VI: Tránh chia cho 0 khi là livestream hoặc không biết thời lượng.
        return "░" * size
    filled = int((position / length) * size)
    return "▓" * filled + "░" * (size - filled)


def get_loop_status(mode) -> str:
    """
    EN: Return a human-readable label for the current queue loop mode.
    VI: Trả về nhãn dễ đọc cho chế độ lặp queue hiện tại.

    Args:
        mode: EN: A wavelink.QueueMode enum value.
              VI: Giá trị enum wavelink.QueueMode.

    Returns:
        EN: Emoji + label string describing the loop state.
        VI: Chuỗi emoji + nhãn mô tả trạng thái lặp.
    """
    return {
        wavelink.QueueMode.loop:     "🔂 Loop bài",       # EN: single track loop / VI: lặp bài hiện tại
        wavelink.QueueMode.loop_all: "🔁 Loop tất cả",    # EN: loop entire queue  / VI: lặp toàn bộ queue
        wavelink.QueueMode.normal:   "➡️ Thường"          # EN: no loop            / VI: không lặp
    }.get(mode, "➡️ Thường")
