"""
subagents/evaluator_prompt.py
------------------------------
Builds the Claude prompt used to score a candidate's answer.
Imported by evaluator_agent.py only.

Scoring dimensions (all 0.0 - 1.0):
  relevance     — did they actually answer the question?
  star_score    — did they use Situation/Task/Action/Result structure?
  depth         — did they go beyond surface level?
  claim_backing — did they back up claims with real examples?
  keywords      — did they hit the expected keywords for this question?
"""


def build_evaluation_prompt(
    question: dict,
    answer_transcript: str,
    persona: str,
    target_role: str,
) -> str:
    expected_kw = ", ".join(question.get("expected_keywords", []))
    q_text = question.get("question", "")
    q_type = question.get("type", "behavioral")

    return f"""
You are an expert interview evaluator assessing a candidate for the role of {target_role}.
The interview persona was: {persona}.
Question type: {q_type}

QUESTION ASKED:
{q_text}

CANDIDATE'S ANSWER:
{answer_transcript}

EXPECTED KEYWORDS (presence signals depth): {expected_kw}

Score the answer on each dimension from 0.0 to 1.0.
Respond ONLY with a valid JSON object — no preamble, no markdown:

{{
  "relevance": 0.0,
  "star_score": 0.0,
  "depth": 0.0,
  "claim_backing": 0.0,
  "keywords": 0.0,
  "overall": 0.0,
  "one_line_verdict": "short verdict here"
}}

overall = weighted average: relevance(0.3) + star(0.2) + depth(0.2) + claims(0.2) + keywords(0.1)
Be strict. A 0.8+ answer must be genuinely impressive for this role.
""".strip()


def parse_scores(raw: str) -> dict:
    """Parse Claude's JSON response. Returns empty dict on failure."""
    import json
    try:
        clean = raw.strip().replace("```json", "").replace("```", "")
        return json.loads(clean)
    except Exception:
        return {}