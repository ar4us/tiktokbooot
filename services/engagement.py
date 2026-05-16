import time
from models.report import EngagementData, TechData

# Static set of high-impact hashtags for heuristic scoring
HIGH_IMPACT_TAGS = {
    "fyp", "foryou", "viral", "trending", "tiktok", 
    "funny", "dance", "music", "comedy", "duet",
    "foryoupage", "love", "memes", "cute", "follow"
}

def engagement_rate(data: EngagementData) -> float:
    interactions = data.likes + data.comments + data.shares + data.favorites
    return interactions / data.views if data.views else 0.0

def er_label(er: float) -> str:
    if er >= 0.15: return "🔥 High"
    if er >= 0.05: return "📈 Medium"
    return "📉 Low"

def views_per_day(data: EngagementData) -> float:
    # upload_timestamp is in seconds (unix)
    if not data.upload_timestamp:
        return 0.0
    age_sec = time.time() - data.upload_timestamp
    age_days = max(age_sec / 86400, 1) # min 1 day to avoid div by zero or huge spikes
    return data.views / age_days

def virality_score(data: EngagementData) -> float:
    """Ratio of shares to views. High shares usually mean high virality."""
    return data.shares / data.views if data.views else 0.0

def hashtag_score(hashtags: list[str]) -> int:
    """Heuristic score 0-100 based on hashtag count and impact."""
    if not hashtags:
        return 0
    base = min(len(hashtags) * 10, 50)
    bonus = sum(10 for h in hashtags if h.lower() in HIGH_IMPACT_TAGS)
    return min(base + bonus, 100)

def quality_label(tech: TechData | None) -> str:
    if not tech:
        return "Unknown"
    if tech.fps >= 50 and tech.bitrate_kbps >= 4000: return "Optimal (60fps High Bitrate)"
    if tech.fps >= 25 and tech.bitrate_kbps >= 2000: return "High (HD Standard)"
    return "Standard"
