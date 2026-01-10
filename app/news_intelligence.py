from typing import List, Tuple
from .models import NewsItem, NewsIntelligence, NewsSignal, PipelineStageState
import re

class NewsIntelligenceEngine:
    """Institutional-grade News Signal & Noise Filtration Engine"""

    # Keywords that indicate "Narrative Exhaust" (Retail Noise)
    NOISE_KEYWORDS = [
        r"best momentum", r"top stocks", r"stocks to watch", 
        r"is it too late", r"strong buy", r"buy these", 
        r"emerging ai", r"must-buy", r"analyst blog"
    ]

    # Keywords that indicate "Primary Signals" (Institutional Alpha)
    SIGNAL_KEYWORDS = [
        r"earnings", r"revenue", r"guidance", r"contract", 
        r"sec filing", r"10-q", r"10-k", r"acquisition", 
        r"merger", r"ceo", r"cfo", r"dividend", r"buyback"
    ]

    @classmethod
    def analyze_feed(cls, ticker: str, news: List[NewsItem]) -> NewsIntelligence:
        if not news:
            return NewsIntelligence(
                signal_score=0, noise_ratio=0, source_diversity=0,
                narrative_trap_warning=False, summary="No news data available for analysis."
            )

        signals: List[NewsSignal] = []
        noise_count = 0
        publishers = set()

        for item in news:
            publishers.add(item.publisher.lower())
            score, category, is_primary = cls._score_headline(item.title)
            
            if score < 0:
                noise_count += 1
            
            signals.append(NewsSignal(
                headline=item.title,
                signal_strength=score,
                impact_category=category,
                is_primary_source=is_primary
            ))

        # Calculate Metrics
        total = len(news)
        noise_ratio = (noise_count / total) * 100 if total > 0 else 0
        source_diversity = len(publishers) / total if total > 0 else 0
        
        # Aggregate Signal Score
        avg_signal = sum([s.signal_strength for s in signals]) / total if total > 0 else 0
        
        # Divergence / Trap Logic
        # A trap is triggered by high noise + low diversity + high retail hype score
        # Note: avg_signal will be positive if headlines are hyped (Strong Buy), 
        # but we classify them as noise.
        is_trap = (noise_ratio > 60 and source_diversity < 0.3)

        summary = f"News feed dominated by {noise_ratio:.0f}% retail narrative noise. "
        if source_diversity < 0.2:
            summary += "Critical lack of publisher diversity detected."
        else:
            summary += "Moderate source diversity."

        if is_trap:
            summary += " WARNING: Narrative Trap Detected. News is price-following noise."

        return NewsIntelligence(
            signal_score=round(avg_signal, 2),
            noise_ratio=round(noise_ratio, 2),
            source_diversity=round(source_diversity, 2),
            narrative_trap_warning=is_trap,
            summary=summary
        )

    @classmethod
    def _score_headline(cls, title: str) -> Tuple[float, str, bool]:
        """Classify and score a single headline"""
        title_clean = title.lower()
        
        # Default
        score = 0
        category = "Neutral"
        is_primary = False

        # Check for Noise (Penalize)
        for pattern in cls.NOISE_KEYWORDS:
            if re.search(pattern, title_clean):
                return -50.0, "Hype/Noise", False

        # Check for Signals (Reward)
        for pattern in cls.SIGNAL_KEYWORDS:
            if re.search(pattern, title_clean):
                return 80.0, "Fundamental", True

        # Check for broad positive/negative sentiment (Low confidence)
        if any(w in title_clean for w in ["rally", "up", "rise", "gain"]):
            score = 20.0
            category = "Momentum"
        elif any(w in title_clean for w in ["drop", "pullback", "down", "fall", "loss"]):
            score = -20.0
            category = "Momentum"

        return score, category, False
