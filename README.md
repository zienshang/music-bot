# 🎵 Music Bot

Bot nhạc Discord hỗ trợ **YouTube**, **Spotify**, **SoundCloud** — sử dụng [wavelink](https://github.com/PythonistaGuild/WaveLink) + Lavalink.

## ✨ Tính năng

| Lệnh | Mô tả |
|---|---|
| `-play <tên/link>` | Phát nhạc từ YouTube, Spotify, SoundCloud |
| `-addtrack <tên/link>` | Thêm bài vào queue (không phát ngay) |
| `-skip` | Bỏ qua bài đang phát |
| `-queue` | Xem danh sách phát |
| `-shuffle` | Trộn ngẫu nhiên queue |
| `-loop` | Bật/tắt loop (Tắt → Bài → Tất cả) |
| `-volume <0-1000>` | Chỉnh âm lượng |
| `-leave` | Bot rời voice channel |
| `-clear` | Xóa toàn bộ queue |

## 🚀 Cài đặt

### 1. Clone repo

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Cài dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình `.env`

```bash
cp .env.example .env
```

Mở `.env` và điền thông tin:

```env
TOKEN=your_bot_token_here
LAVALINK_URI=http://127.0.0.1:2333
LAVALINK_PASSWORD=youshallnotpass
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

### 4. Chạy Lavalink

Tải [Lavalink.jar](https://github.com/lavalink-devs/Lavalink/releases) và chạy:

```bash
java -jar Lavalink.jar
```

### 5. Chạy bot

```bash
python main.py
```

## 📦 Requirements

```
discord.py
wavelink
python-dotenv
```

## 📁 Cấu trúc thư mục

```
├── main.py
├── config.py
├── .env              ← KHÔNG commit (đã có trong .gitignore)
├── .env.example      ← Template để người khác tự tạo .env
├── cogs/
│   └── music/
│       ├── play.py
│       ├── addtrack.py
│       ├── skip.py
│       ├── queue.py
│       ├── shuffle.py
│       ├── loop.py
│       ├── volume.py
│       ├── leave.py
│       └── clear_queue.py
└── utils/
    ├── help.py
    ├── helpers.py
    ├── nowplaying.py
    └── status.py
```
