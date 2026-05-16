from models.report import EngagementData, TechData, InsightReport
from services import engagement as engine

class InsightBuilder:
    @staticmethod
    def build(engagement: EngagementData, tech: TechData | None) -> InsightReport:
        er = engine.engagement_rate(engagement)
        
        return InsightReport(
            tech=tech or TechData("Unknown", 0, "unknown", 0, 0, []),
            engagement=engagement,
            engagement_rate=round(er * 100, 1),
            er_label=engine.er_label(er),
            views_per_day=round(engine.views_per_day(engagement)),
            virality_score=round(engine.virality_score(engagement) * 100, 2),
            quality_label=engine.quality_label(tech),
            hashtag_score=engine.hashtag_score(engagement.hashtags),
            audio_trending=bool(engagement.sound_title) # Simple proxy for now
        )
