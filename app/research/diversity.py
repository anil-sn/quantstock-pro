from typing import List, Dict, Set
from ..models import SourceCategory, ResearchSource, SourceDiversity
import re

class SourceDiversityManager:
    """Classifies sources and calculates institutional diversity metrics"""

    CATEGORY_PATTERNS = {
        SourceCategory.GOVERNMENT: [r"\.gov", r"sec\.gov", r"edgar"],
        SourceCategory.ACADEMIC: [r"\.edu", r"scholar", r"researchgate", r"ssrn"],
        SourceCategory.PRIMARY_CORPORATE: [r"ir\.", r"investor", r"shareholder", r"calix\.com", r"apple\.com", r"newsroom", r"press-release"],
        SourceCategory.NEWS: [r"reuters\.com", r"bloomberg\.com", r"wsj\.com", r"ft\.com", r"cnbc\.com", r"yahoo\.com"],
        SourceCategory.ANALYSIS: [r"seekingalpha", r"morningstar", r"zacks", r"fool\.com", r"barrons"]
    }

    @classmethod
    def classify_source(cls, title: str, url: str) -> ResearchSource:
        url_lower = url.lower()
        category = SourceCategory.OTHER
        credibility = 0.5

        for cat, patterns in cls.CATEGORY_PATTERNS.items():
            if any(re.search(p, url_lower) for p in patterns):
                category = cat
                # Government and Primary Corporate get higher weight
                if cat in [SourceCategory.GOVERNMENT, SourceCategory.PRIMARY_CORPORATE]:
                    credibility = 0.9
                elif cat == SourceCategory.ACADEMIC:
                    credibility = 0.8
                elif cat == SourceCategory.NEWS:
                    credibility = 0.7
                break

        return ResearchSource(
            title=title,
            url=url,
            category=category,
            credibility_score=credibility
        )

    @classmethod
    def calculate_diversity(cls, sources: List[ResearchSource]) -> SourceDiversity:
        if not sources:
            return SourceDiversity(
                category_distribution={},
                overall_diversity_score=0,
                is_diversified=False
            )

        dist = {cat: 0 for cat in SourceCategory}
        unique_publishers = set()

        for s in sources:
            dist[s.category] += 1
            # Extract basic domain as proxy for publisher
            domain = re.sub(r"https?://(www\.)?", "", s.url).split("/")[0]
            unique_publishers.add(domain)

        # Shannon-like diversity score based on categories + publishers
        active_cats = sum(1 for v in dist.values() if v > 0)
        cat_score = active_cats / len(SourceCategory)
        
        pub_ratio = len(unique_publishers) / len(sources)
        
        overall = (cat_score * 0.6) + (pub_ratio * 0.4)
        
        bias_warning = None
        if dist[SourceCategory.NEWS] / len(sources) > 0.7:
            bias_warning = "High Media Dependency: Feed dominated by news aggregators."
        elif dist[SourceCategory.OTHER] > dist[SourceCategory.GOVERNMENT]:
            bias_warning = "Low Primary Authority: Lack of official SEC/Government sourcing."

        return SourceDiversity(
            category_distribution=dist,
            overall_diversity_score=round(overall, 2),
            is_diversified=overall > 0.5,
            bias_warning=bias_warning
        )
