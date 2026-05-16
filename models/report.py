from dataclasses import dataclass

@dataclass
class TechData:
    resolution: str          # "1080x1920"
    fps: float               # 59.94
    codec: str               # "h264"
    bitrate_kbps: int        # 4200
    size_mb: float           # 56.0
    formats: list[dict]      # all available formats from yt-dlp

@dataclass
class EngagementData:
    views: int
    likes: int
    comments: int
    shares: int
    favorites: int
    upload_timestamp: int    # unix
    hashtags: list[str]
    sound_title: str | None
    duration_sec: int
    uploader: str
    description: str
    video_id: str = "Unknown"
    source: str = "Browser"
    region: str = "Global"
    is_shadow_banned: bool = False
    title: str = ""
    video_url: str | None = None
    formats: list[dict] = None
    http_headers: dict = None

@dataclass
class InsightReport:
    tech: TechData
    engagement: EngagementData
    # computed
    engagement_rate: float   # (likes+comments+shares+favs) / views
    er_label: str            # "Low" / "Medium" / "High"
    views_per_day: float
    virality_score: float    # shares / views
    quality_label: str       # "Optimal" / "High" / "Standard"
    hashtag_score: int       # 0-100 heuristic
    audio_trending: bool
