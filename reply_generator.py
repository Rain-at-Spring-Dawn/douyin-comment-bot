"""Generate AI-powered replies for Douyin comments."""
import random
from typing import List, Optional

from rich.console import Console

from config import config

console = Console()


class ReplyGenerator:
    """Generate contextual replies to comments using LLM."""

    def __init__(self):
        self.client = None
        self.model = config.openai_model
        if config.openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=config.openai_base_url,
                api_key=config.openai_api_key,
            )

    def generate_reply(self, video_title: str, comment_content: str) -> Optional[str]:
        """Generate a single reply for a comment."""
        if not self.client or not config.openai_api_key:
            return self._fallback_reply()

        prompt = config.reply_prompt_template.format(
            video_title=video_title or "抖音视频",
            comment_content=comment_content or "",
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.8,
            )
            content = response.choices[0].message.content or ""

            # Some reasoning models put the answer in reasoning_content
            if not content.strip():
                reasoning = getattr(response.choices[0].message, "reasoning_content", None)
                if reasoning:
                    # Extract the last sentence as reply
                    import re
                    sentences = re.findall(r'[^。！？]*[。！？]', reasoning)
                    if sentences:
                        content = sentences[-1].strip()

            reply = content.strip('"').strip("'").strip()
            if reply:
                console.print(f"[dim]🤖 AI生成: {reply}[/dim]")
                return reply
            return self._fallback_reply()

        except Exception as e:
            console.print(f"[yellow]AI生成失败: {e}，使用预设回复[/yellow]")
            return self._fallback_reply()

    def _fallback_reply(self) -> str:
        """Fallback replies when AI is unavailable."""
        fallbacks = [
            "哈哈，说得对！",
            "有道理！👍",
            "确实如此～",
            "赞同！",
            "哈哈😄",
            "说得不错！",
            "有见解！",
            "感谢评论～",
            "没错！",
            "是的是的！",
        ]
        return random.choice(fallbacks)

    def batch_generate(self, video_title: str, comments: List[dict]) -> List[dict]:
        """Generate replies for multiple comments."""
        results = []
        for comment in comments:
            reply = self.generate_reply(video_title, comment.get("content", ""))
            results.append({
                **comment,
                "ai_reply": reply or "",
            })
        return results
