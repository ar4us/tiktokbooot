import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from models.report import InsightReport

class TelegramFormatter:
    @staticmethod
    def format_number(n: int) -> str:
        """Formats numbers with commas: 24343327 -> 24,343,327"""
        return f"{n:,}"

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Formats seconds into mm:ss: 16 -> 0:16, 75 -> 1:15"""
        if not seconds:
            return "0:00"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

    @staticmethod
    def format_bitrate(kbps: int) -> str:
        """Formats bitrate: 28300 -> 28.3 Mbps"""
        if not kbps:
            return "0 Kbps"
        if kbps >= 1000:
            return f"{kbps/1000:.1f} Mbps"
        return f"{kbps} Kbps"

    @staticmethod
    def format_fps(fps: float) -> str:
        """Formats FPS with premium labels."""
        if not fps:
            return "30 (Standard)"
        
        label = "Standard"
        if fps >= 100:
            label = "Ultra Smooth"
        elif fps >= 50:
            label = "Smooth"
        elif fps >= 23: # Catch 23.98, 24, 25, 29.97, 30
            label = "Standard"
        else:
            label = "Cinematic"
            
        fps_val = f"{fps:.0f}" if fps % 1 == 0 else f"{fps:.2f}"
        return f"{fps_val} ({label})"

    @staticmethod
    def get_region_display(code: str) -> str:
        """Converts region code to flag and name."""
        regions = {
            "BR": "🇧🇷 Brazil",
            "US": "🇺🇸 USA",
            "ID": "🇮🇩 Indonesia",
            "RU": "🇷🇺 Russia",
            "VN": "🇻🇳 Vietnam",
            "MX": "🇲🇽 Mexico",
            "PH": "🇵🇭 Philippines",
            "TH": "🇹🇭 Thailand",
            "TR": "🇹🇷 Turkey",
            "PK": "🇵🇰 Pakistan",
            "FR": "🇫🇷 France",
            "DE": "🇩🇪 Germany",
            "GB": "🇬🇧 UK",
            "ES": "🇪🇸 Spain",
            "IT": "🇮🇹 Italy",
            "JP": "🇯🇵 Japan",
            "KR": "🇰🇷 South Korea",
            "MY": "🇲🇾 Malaysia",
            "SG": "🇸🇬 Singapore",
            "GL": "🌎 Global",
            "GLOBAL": "🌎 Global"
        }
        return regions.get(code.upper(), f"📍 {code}")

    @staticmethod
    def format_compact(n: int) -> str:
        """Formats numbers into K/M: 1200 -> 1.2K, 1200000 -> 1.2M"""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    @staticmethod
    def get_progress_bar(percentage: float, length: int = 10) -> str:
        """Generates a visual progress bar: [■■■□□□□□□□]"""
        filled = int(round(percentage / 100 * length))
        if filled > length: filled = length
        if filled < 0: filled = 0
        return "■" * filled + "□" * (length - filled)

    @classmethod
    def format_report(cls, report: InsightReport, url_hash: str) -> tuple[str, InlineKeyboardMarkup]:
        engagement = report.engagement
        tech = report.tech
        
        # Helper for HTML escaping
        hesc = html.escape
        
        uploader = hesc(engagement.uploader)
        res = hesc(tech.resolution)
        codec = hesc(tech.codec).upper()
        er_label = hesc(report.er_label)
        q_label = hesc(report.quality_label)
        
        # Formatted Metrics
        views = cls.format_compact(engagement.views)
        likes = cls.format_compact(engagement.likes)
        comments = cls.format_compact(engagement.comments)
        shares = cls.format_compact(engagement.shares)
        favs = cls.format_compact(engagement.favorites)
        
        duration = cls.format_duration(engagement.duration_sec)
        fps_label = cls.format_fps(tech.fps)
        bitrate = cls.format_bitrate(tech.bitrate_kbps)
        size = f"{tech.size_mb:.1f} MB"
        
        er = f"{report.engagement_rate:.2f}"
        virality = f"{report.virality_score:.2f}"
        vpd = cls.format_compact(int(report.views_per_day))
        h_score = str(report.hashtag_score)
        region_display = cls.get_region_display(engagement.region)
        hashtags = " ".join(engagement.hashtags[:5]) if engagement.hashtags else "None"
        music = engagement.sound_title or "Original Sound"

        # Progress Bars (Heuristic: ER max 20%, Virality max 10%)
        er_progress = cls.get_progress_bar(min(report.engagement_rate * 5, 100)) # 20% ER is 100% full
        vir_progress = cls.get_progress_bar(min(report.virality_score * 10, 100)) # 10% Virality is 100% full

        # Dashboard Construction (HTML)
        msg = (
            f"<b>🚀 TIKTOK ANALYTICS INSIGHTS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>@{uploader}</b>  ┃  ⏱ <b>{duration}</b>\n"
            f"🎬 <code>{hesc(engagement.title[:40]) + '...' if len(engagement.title) > 40 else hesc(engagement.title)}</code>\n\n"
            
            f"<b>📊 PERFORMANCE METRICS</b>\n"
            f"┃ ❤️ Likes: <code>{likes}</code>\n"
            f"┃ 📈 ER: <code>{er}%</code> | {er_progress}\n"
            f"┃ ✨ Potential: <b>{er_label}</b>\n"
            f"┃ 🚀 Virality: <code>{virality}%</code> | {vir_progress}\n"
            f"┃ 📅 Avg Growth: <code>{vpd} vpd</code>\n\n"
            
            f"<b>⚙️ TECHNICAL ANALYSIS</b>\n"
            f"┃ 📺 Res: <code>{res}</code>\n"
            f"┃ 🎞 FPS: <code>{fps_label}</code>\n"
            f"┃ 🎥 Codec: <code>{codec}</code>\n"
            f"┃ ⚡ Bitrate: <code>{bitrate}</code>\n"
            f"┃ 📦 Size: <code>{size}</code>\n\n"
 
            f"<b>📍 DATA POINT</b>\n"
            f"┃ • Region | {region_display}\n"
            f"┃ • Views | {views}\n"
            f"┃ • Shares | {shares}\n"
            f"┃ • Saves | {favs}\n"
            f"┃ • Music | {hesc(music[:25])}\n\n"
            
            f"<b>🧠 AI CONTENT SCORE</b>\n"
            f"┃ 🏷 Tags: <code>{h_score}/100</code>\n"
            f"┃ 💎 Quality: <b>{q_label}</b>\n"
            f"┃ 🎵 Audio: {'🔥 Trending' if report.audio_trending else 'Standard'}\n"
            f"┃ 👻 Shadowban: <b>{'⚠️ Detected' if engagement.is_shadow_banned else '✅ Clear'}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        # Build keyboard
        keyboard = [
            [
                InlineKeyboardButton("📥 Download Video", callback_data=f"dl_vid_{url_hash}"),
                InlineKeyboardButton("🎵 Get Audio", callback_data=f"dl_aud_{url_hash}")
            ],
            [InlineKeyboardButton("📋 Change Quality", callback_data="list_qual")]
        ]
        
        return msg, InlineKeyboardMarkup(keyboard)
