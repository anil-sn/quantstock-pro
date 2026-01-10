from typing import List, Set
from ..models import Finding, ResearchSource

class FindingsRepository:
    """Manages accumulated knowledge and prevents redundant research"""

    def __init__(self):
        self.findings: List[Finding] = []
        self.sources: List[ResearchSource] = []
        self._seen_facts: Set[str] = set()

    def add_iteration_results(self, findings: List[Finding], sources: List[ResearchSource]):
        # Offset finding indices by current source list length
        offset = len(self.sources)
        
        for f in findings:
            # Simple deduplication based on content
            fact_key = f.fact.lower().strip()
            if fact_key not in self._seen_facts:
                f.citation_indices = [idx + offset for idx in f.citation_indices]
                self.findings.append(f)
                self._seen_facts.add(fact_key)

        self.sources.extend(sources)

    def get_all_sources(self) -> List[ResearchSource]:
        return self.sources

    def get_all_findings(self) -> List[Finding]:
        return self.findings

    def format_for_ai(self) -> str:
        """Formats findings with IEEE-style citations for AI synthesis"""
        lines = []
        for i, f in enumerate(self.findings):
            citations = "".join([f"[{idx + 1}]" for idx in f.citation_indices])
            lines.append(f"{i+1}. {f.fact} {citations}")
        return "\n".join(lines)

    def format_sources_list(self) -> str:
        lines = []
        for i, s in enumerate(self.sources):
            lines.append(f"[{i+1}] {s.title} ({s.category.value}): {s.url}")
        return "\n".join(lines)
