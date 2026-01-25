import json
from typing import Dict, List

from src.agents.base_agent import BaseAgent


EDITOR_SYSTEM_PROMPT = """
You are an expert Slidev Developer and Presentation Designer.
Your task is to transform raw text into beautiful, structured Slidev markdown slides.

Rules (must follow):
1. The document must start with Frontmatter (global config). Each slide can also have Frontmatter.
2. Use `---` to separate slides.
3. Use valid Slidev layouts via `layout` in Frontmatter (e.g., `cover`, `default`, `intro`, `center`, `two-cols`, `two-cols-header`, `image-left`, `image-right`, `full`, `end`).
4. For `two-cols`, put left content first, then `::right::` for right content.
5. For `image-left` / `image-right`, set `image` field in Frontmatter and place content on the other side.
6. Keep text concise and readable. Prefer bullet points and short sentences.
7. Use standard Markdown for emphasis, links, and inline code. Do NOT wrap the whole output in a Markdown code block.
8. Use Slidev features when helpful: `v-click` / `<v-clicks>` for progressive reveals, icons like `<mdi-account />`, and images with Markdown or `<img>`.
9. Ensure Slidev markdown is syntactically correct and renderable.
10. Provide a title slide, outline slide, content slides, conclusion, and thanks/end slide.
""".strip()


class EditorAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(role="Editor", model_name=model_name)
        self.set_system_prompt(EDITOR_SYSTEM_PROMPT)

    def generate_draft(self, raw_content: str) -> str:
        prompt = (
            "Please convert the following content into Slidev markdown slides. "
            "Return the full slides.md content only.\n\n"
            f"Content:\n{raw_content}\n"
        )
        response = self.chat(prompt)
        return response.content.strip()

    def refine_slides(self, current_code: str, feedback: List[Dict]) -> str:
        feedback_text = json.dumps(feedback, ensure_ascii=False, indent=2)
        prompt = (
            "Please refine the Slidev markdown according to the feedback. "
            "Return the full revised slides.md content only.\n\n"
            f"Current Slides:\n{current_code}\n\n"
            f"Feedback (JSON):\n{feedback_text}\n"
        )
        response = self.chat(prompt)
        return response.content.strip()
