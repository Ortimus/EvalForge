"""
LLMJudgeScorer — uses an LLM (default: Claude) to score open-ended responses.
Returns a 1-5 score plus the judge's rationale for auditability.
"""
import anthropic


class LLMJudgeScorer:

    SYSTEM_PROMPT = """You are a precise, consistent evaluation judge.
Score responses strictly according to the rubric provided.
Always respond in JSON with keys: score (int 1-5), rationale (str)."""

    def __init__(self, judge_model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic()
        self.judge_model = judge_model

    def score(self, response: str, rubric: str, task_prompt: str = "") -> dict:
        user_message = f"""
Task prompt:
{task_prompt}

Model response:
{response}

Rubric:
{rubric}

Return only valid JSON.
"""
        message = self.client.messages.create(
            model=self.judge_model,
            max_tokens=512,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        import json
        return json.loads(message.content[0].text)
