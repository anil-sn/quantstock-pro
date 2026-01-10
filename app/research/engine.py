import json
from typing import List, Optional
from ..models import ResearchReport, ResearchIteration, Finding, ResearchSource, PipelineStageState, SourceDiversity
from .diversity import SourceDiversityManager
from .repository import FindingsRepository
from ..ai import client, sanitize_prompt_text
from ..logger import pipeline_logger
from google.genai import types

class ResearchEngine:
    """Orchestrates iterative searches and finding extraction"""

    def __init__(self, search_tool):
        self.search_tool = search_tool
        self.repository = FindingsRepository()

    async def execute_deep_research(self, ticker: str, max_iterations: int = 2) -> ResearchReport:
        iterations: List[ResearchIteration] = []
        
        # Iteration 1: Broad Quantitative Discovery
        base_query = f"{ticker} investor relations primary risk factors guidance 2025 2026"
        iter1 = await self._run_iteration(ticker, base_query, iteration_num=1)
        iterations.append(iter1)
        
        # Iteration 2: Targeted Deep-Dive
        followup_query = f"{ticker} SEC filings 10-K 10-Q analyst consensus controversy 2025"
        iter2 = await self._run_iteration(ticker, followup_query, iteration_num=2)
        iterations.append(iter2)

        # --- Terminal Check for Grounding ---
        all_findings = self.repository.get_all_findings()
        diversity = SourceDiversityManager.calculate_diversity(self.repository.get_all_sources())
        
        if not all_findings:
            synthesis = f"## Research Aborted: No Grounding Data Found\nDeep research for {ticker} yielded no primary or secondary source findings after {max_iterations} iterations. No synthesis possible."
        else:
            synthesis = await self._synthesize_report(ticker, diversity)

        return ResearchReport(
            ticker=ticker,
            synthesis=synthesis,
            iterations=iterations,
            diversity_metrics=diversity,
            total_sources=len(self.repository.get_all_sources())
        )

    async def _run_iteration(self, ticker: str, query: str, iteration_num: int) -> ResearchIteration:
        # 1. Search
        search_results = await self.search_tool(query=query)
        if not search_results:
            pipeline_logger.log_event(ticker, "RESEARCH", "SILENCE", f"Iteration {iteration_num}: No search results")
            return ResearchIteration(query=query, findings=[], sources=[])
        
        pipeline_logger.log_payload(ticker, "RESEARCH", f"ITER_{iteration_num}_SEARCH_RAW", search_results)

        # 2. Extract Sources
        sources: List[ResearchSource] = []
        raw_snippets = []
        
        for i, res in enumerate(search_results[:5]):
            source = SourceDiversityManager.classify_source(res.get('title', 'Unknown'), res.get('link', ''))
            sources.append(source)
            raw_snippets.append(f"Source [{i}]: {res.get('title')} - {res.get('snippet')}")

        # 3. Use AI to extract "Atomic Findings"
        findings = await self._extract_findings(ticker, "\n".join(raw_snippets), iteration_num)
        pipeline_logger.log_payload(ticker, "RESEARCH", f"ITER_{iteration_num}_FINDINGS", [f.model_dump() for f in findings])
        
        # 4. Add to Repository
        if findings:
            self.repository.add_iteration_results(findings, sources)
        
        return ResearchIteration(
            query=query,
            findings=findings,
            sources=sources
        )

    async def _extract_findings(self, ticker: str, context: str, iter_num: int) -> List[Finding]:
        prompt = f"""
        Extract up to 5 atomic financial or risk findings for {ticker} from the following snippets.
        Each finding MUST be a single factual sentence.
        Cite the source using the index provided in the snippet (e.g. [0], [1]).
        
        STRICT GROUNDING RULE: If the snippets are empty, irrelevant, or do not contain specific facts about {ticker}, return ONLY an empty JSON list []. Do not explain yourself.
        
        SNIPPETS:
        {context}
        
        OUTPUT FORMAT: Valid JSON list of objects:
        [{{"fact": "string", "citation_indices": [number]}}]
        """
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            
            if not text or text == "[]":
                return []
                
            data = json.loads(text)
            return [Finding(fact=d['fact'], citation_indices=d['citation_indices'], iteration=iter_num) for d in data]
        except Exception as e:
            print(f"Finding Extraction Error: {e}")
            return []

    async def _synthesize_report(self, ticker: str, diversity: SourceDiversity) -> str:
        findings_text = self.repository.format_for_ai()
        sources_text = self.repository.format_sources_list()
        
        prompt = f"""
        Synthesize a professional investment research executive summary for {ticker} based STRICTLY on these findings.
        Use IEEE citation style [1], [2] throughout.
        
        STRICT GROUNDING RULES:
        1. Only use the provided findings.
        2. Do not manufacture citations or facts.
        3. If diversity is low, explicitly warn about narrative traps.
        
        DIVERSITY AUDIT:
        - Score: {diversity.overall_diversity_score}
        - Warning: {diversity.bias_warning}
        
        FINDINGS:
        {findings_text}
        
        SOURCES:
        {sources_text}
        
        Limit to 3 concise paragraphs.
        """
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Synthesis Failed: {e}"
