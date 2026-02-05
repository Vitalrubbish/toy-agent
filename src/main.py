import json
import os
import shutil
import time
from pathlib import Path
from typing import List

import typer
from dotenv import load_dotenv

from agents.editor import EditorAgent
from agents.critic import CriticAgent
from utils.llm_client import LLMClient
from utils.slidev_runner import SlidevRunner, RenderError


app = typer.Typer(add_completion=False)


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def clear_dir(path: str) -> None:
    if Path(path).exists():
        shutil.rmtree(path)
    Path(path).mkdir(parents=True, exist_ok=True)


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip() + "\n"
    return text

def is_approved(feedback: List[dict]) -> bool:
    return not feedback


def _read_json_file(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}



def generate_iteration_summary_report(
    logs_dir: str,
    mode: str,
    run_stamp: str,
    total_iterations: int,
    iteration_metrics: List[dict],
    total_input_tokens: int,
    total_output_tokens: int,
    total_cost: float,
) -> str:
    report_path = os.path.join(logs_dir, f"iteration_summary_{run_stamp}.md")
    lines: List[str] = []
    lines.append(f"# Iteration Summary Report ({mode} mode)")
    lines.append("")
    lines.append(f"- Run Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Total Iterations: {total_iterations}")
    lines.append(f"- Total Input Tokens: {total_input_tokens}")
    lines.append(f"- Total Output Tokens: {total_output_tokens}")
    lines.append(f"- Estimated Cost: ${total_cost:.4f}")
    if iteration_metrics:
        avg_iter_time = sum(item.get("duration_seconds", 0) for item in iteration_metrics) / len(
            iteration_metrics
        )
        lines.append(f"- Avg Iteration Time: {avg_iter_time:.2f}s")
    lines.append("")

    for idx in range(1, total_iterations + 1):
        lines.append(f"## Iteration {idx}")

        iteration_metric = (
            iteration_metrics[idx - 1] if idx - 1 < len(iteration_metrics) else {}
        )
        if iteration_metric:
            lines.append("### Iteration Metrics")
            lines.append(f"- Duration: {iteration_metric.get('duration_seconds', 0):.2f}s")
            lines.append(f"- Input Tokens: {iteration_metric.get('input_tokens', 0)}")
            lines.append(f"- Output Tokens: {iteration_metric.get('output_tokens', 0)}")
            if iteration_metric.get("agent_breakdown"):
                lines.append("- Agent Breakdown:")
                for agent_name, usage in iteration_metric["agent_breakdown"].items():
                    lines.append(
                        f"  - {agent_name}: input {usage.get('input_tokens', 0)}, output {usage.get('output_tokens', 0)}, cost ${usage.get('cost', 0.0):.4f}"
                    )
            lines.append("")

        critic_iter_log_path = os.path.join(logs_dir, f"iter_{idx}_critic.txt")
        critic_payload = _read_json_file(critic_iter_log_path)
        critic_feedback = critic_payload.get("feedback", []) if isinstance(critic_payload, dict) else []
        critic_summary = critic_payload.get("summary", {}) if isinstance(critic_payload, dict) else {}

        lines.append("### Critic Feedback")
        if not critic_feedback:
            lines.append("- No feedback (approved)")
        else:
            for item in critic_feedback:
                page_index = item.get("page_index", "N/A")
                severity = item.get("severity", "UNKNOWN")
                issue = item.get("issue", "No issue")
                suggestion = item.get("suggestion", "No suggestion")
                category = item.get("category") or ""
                category_text = f" ({category})" if category else ""
                lines.append(
                    f"- [Page {page_index}] **{severity}**{category_text}: {issue}"
                )
                lines.append(f"  - Suggestion: {suggestion}")

        if critic_summary:
            lines.append("")
            lines.append("**Critic Summary**")
            lines.append("```json")
            lines.append(json.dumps(critic_summary, ensure_ascii=False, indent=2))
            lines.append("```")

        lines.append("")

    write_text_file(report_path, "\n".join(lines).strip() + "\n")
    return report_path

@app.command()
def run(
    input_path: str = "data/paper_summary.txt",
    output_dir: str = "outputs",
    max_iterations: int = 5,
    model_name: str = "gpt-4o",
    mode: str = "dual", # single / dual
):
    """Run the PPT-Agent pipeline."""
    load_dotenv()
    start_time = time.time()

    raw_content = read_text_file(input_path)

    default_model = model_name or "gpt-4o"

    editor_provider = os.getenv("EDITOR_LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "openai")
    critic_provider = os.getenv("CRITIC_LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "openai")

    editor_model = os.getenv("EDITOR_LLM_MODEL") or os.getenv("LLM_MODEL") or default_model
    critic_model = os.getenv("CRITIC_LLM_MODEL") or os.getenv("LLM_MODEL") or default_model

    if os.getenv("EDITOR_LLM_MODEL") is None and os.getenv("LLM_MODEL") is None:
        if editor_provider == "openai":
            editor_model = "gpt-4o"
        else:
            print("模型未指定，供应商不是OpenAI")
            exit(1)

    if os.getenv("CRITIC_LLM_MODEL") is None and os.getenv("LLM_MODEL") is None:
        if critic_provider == "openai":
            critic_model = "gpt-4o"
        else:
            print("模型未指定，供应商不是OpenAI")
            exit(1)

    editor = EditorAgent(model_name=editor_model, provider=editor_provider)
    critic = None
    if mode == "dual":
        critic = CriticAgent(model_name=critic_model, provider=critic_provider)
    runner = SlidevRunner(work_dir=str(Path(__file__).resolve().parents[1]))

    if mode == "dual":
        output_dir = os.path.join(output_dir, "dual_output")
    else:
        output_dir = os.path.join(output_dir, "single_output")

    current_dir = os.path.join(output_dir, "current")
    history_dir = os.path.join(output_dir, "history")
    logs_dir = os.path.join(output_dir, "logs")
    images_dir = os.path.join(current_dir, "images")
    
    ensure_dir(current_dir)
    ensure_dir(history_dir)
    ensure_dir(logs_dir)

    feedback: List[dict] = []
    slides_md = ""
    outline_md = ""
    last_success_md = ""
    last_render_error: str | None = None
    need_fix = False
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0
    iteration_metrics: List[dict] = []

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_log_path = os.path.join(logs_dir, f"run_{run_stamp}.log")

    def append_run_log(message: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {message}\n"
        with open(run_log_path, "a", encoding="utf-8") as f:
            f.write(line)
        typer.echo(message)

    # Outline
    append_run_log("Editor: generating outline")
    outline_md = editor.generate_outline(raw_content)
    outline_log_path = os.path.join(logs_dir, f"outline_{run_stamp}.md")
    outline_path = os.path.join(current_dir, "outline.md")
    write_text_file(outline_log_path, outline_md)
    write_text_file(outline_path, outline_md)
    append_run_log(f"Outline saved to {outline_path}")

    if not typer.confirm("Outline generated. Start iteration?", default=True):
        append_run_log("User stopped after outline generation.")
        typer.echo(f"Outline saved at {outline_path}")
        return


    # Editor: Slides
    for iteration in range(1, max_iterations + 1):
        
        iteration_start = time.time()
        # editor_adjustments: List[dict] = []
        # editor_summary: dict = {}
        iteration_input_tokens = 0
        iteration_output_tokens = 0
        iteration_cost = 0.0
        agent_breakdown: dict = {}

        append_run_log(f"\nIteration {iteration}/{max_iterations} started")

        # slides.md
        if iteration == 1:
            append_run_log("Editor: generating draft")
            slides_md = editor.generate_draft(raw_content, outline=outline_md)
        elif need_fix:
            append_run_log("Editor: fixing slides after render error")
            slides_md = editor.fix_slides(slides_md, last_render_error or "")
        else:
            append_run_log("Editor: refining slides")
            slides_md = editor.refine_slides(slides_md, feedback)
            

        slides_md = strip_code_fence(slides_md)

        editor_log_path = os.path.join(logs_dir, f"iter_{iteration}_editor.txt")
        editor_output = editor.last_response or slides_md
        write_text_file(editor_log_path, editor_output)
        append_run_log(f"Editor output saved to {editor_log_path}")

        if editor.last_response_usage:
            editor_usage = editor.last_response_usage
            if "input_tokens" in editor_usage:
                editor_input = editor_usage.get("input_tokens", 0)
            else:
                editor_input = editor_usage.get("prompt_tokens", 0)
            if "output_tokens" in editor_usage:
                editor_output = editor_usage.get("output_tokens", 0) + editor_usage.get("reasoning_tokens", 0)
            else:
                editor_output = editor_usage.get("completion_tokens", 0)
            editor_cost = LLMClient.calculate_context_cost(editor_input, editor_output)
            total_input_tokens += editor_input
            total_output_tokens += editor_output
            total_cost += editor_cost
            iteration_input_tokens += editor_input
            iteration_output_tokens += editor_output
            iteration_cost += editor_cost
            agent_breakdown["Editor"] = {
                "input_tokens": editor_input,
                "output_tokens": editor_output,
                "cost": editor_cost,
            }


        # Render
        slides_path = os.path.join(current_dir, "slides.md")
        candidate_path = os.path.join(current_dir, "slides_candidate.md")
        write_text_file(candidate_path, slides_md)
        rendered_log_path = os.path.join(logs_dir, f"iter_{iteration}_rendered.md")
        write_text_file(rendered_log_path, slides_md)
        append_run_log(f"Rendered markdown saved to {rendered_log_path}")

        append_run_log("Rendering slides to images")
        clear_dir(images_dir)
        image_paths = []
        render_error = None
        try:
            image_paths = runner.render_slides(candidate_path, images_dir)
        except RenderError as e:
            render_error = str(e)
            append_run_log("Render failed. Sending error back to editor for fixes")

        if render_error:
            need_fix = True
            last_render_error = render_error
            feedback = [
                {
                    "issue": "Render Error",
                    "details": render_error,
                    "severity": "CRITICAL",
                }
            ]
            critic_log_path = os.path.join(logs_dir, f"iter_{iteration}_critic.txt")
            write_text_file(critic_log_path, json.dumps(feedback, ensure_ascii=False, indent=2))
            append_run_log(f"Render error logged to {critic_log_path}")
        else:
            need_fix = False
            last_render_error = None
            last_success_md = slides_md
            write_text_file(slides_path, slides_md)
            append_run_log(f"Rendered {len(image_paths)} slide images")

            if mode == "dual":
                append_run_log("Critic: reviewing slides")
                feedback = critic.review(image_paths, slides_md=slides_md)
                critic_log_path = os.path.join(logs_dir, f"iter_{iteration}_critic.txt")
                critic_output = critic.last_response or json.dumps(feedback, ensure_ascii=False, indent=2)
                write_text_file(critic_log_path, critic_output)
                append_run_log(f"Critic output saved to {critic_log_path}")

                if critic.last_response_usage:
                    critic_usage = critic.last_response_usage
                    if "input_tokens" in critic_usage:
                        critic_input = critic_usage.get("input_tokens", 0)
                    else:
                        critic_input = critic_usage.get("prompt_tokens", 0)
                    if "output_tokens" in critic_usage:
                        critic_output_tokens = critic_usage.get("output_tokens", 0) + critic_usage.get("reasoning_tokens", 0)
                    else:
                        critic_output_tokens = critic_usage.get("completion_tokens", 0)
                    critic_cost = LLMClient.calculate_context_cost(critic_input, critic_output_tokens)
                    total_input_tokens += critic_input
                    total_output_tokens += critic_output_tokens
                    total_cost += critic_cost
                    iteration_input_tokens += critic_input
                    iteration_output_tokens += critic_output_tokens
                    iteration_cost += critic_cost
                    agent_breakdown["Critic"] = {
                        "input_tokens": critic_input,
                        "output_tokens": critic_output_tokens,
                        "cost": critic_cost,
                    }
            else:
                append_run_log("Editor: self-reviewing slides")
                feedback = editor.self_review(image_paths, slides_md=slides_md)
                critic_log_path = os.path.join(logs_dir, f"iter_{iteration}_critic.txt")
                critic_output = editor.last_response or json.dumps(feedback, ensure_ascii=False, indent=2)
                write_text_file(critic_log_path, critic_output)
                append_run_log(f"Self-review output saved to {critic_log_path}")

                if editor.last_response_usage:
                    review_usage = editor.last_response_usage
                    if "input_tokens" in review_usage:
                        review_input = review_usage.get("input_tokens", 0)
                    else:
                        review_input = review_usage.get("prompt_tokens", 0)
                    if "output_tokens" in review_usage:
                        review_output = review_usage.get("output_tokens", 0) + review_usage.get("reasoning_tokens", 0)
                    else:
                        review_output = review_usage.get("completion_tokens", 0)
                    review_cost = LLMClient.calculate_context_cost(review_input, review_output)
                    total_input_tokens += review_input
                    total_output_tokens += review_output
                    total_cost += review_cost
                    iteration_input_tokens += review_input
                    iteration_output_tokens += review_output
                    iteration_cost += review_cost
                    agent_breakdown["Editor(Self-Review)"] = {
                        "input_tokens": review_input,
                        "output_tokens": review_output,
                        "cost": review_cost,
                    }


        iter_dir = os.path.join(history_dir, f"iter_{iteration}")
        ensure_dir(iter_dir)
        source_slides_path = slides_path if Path(slides_path).exists() else candidate_path
        shutil.copy(source_slides_path, os.path.join(iter_dir, "slides.md"))
        if image_paths:
            images_history = os.path.join(iter_dir, "images")
            clear_dir(images_history)
            for img in image_paths:
                shutil.copy(img, images_history)

        critique_path = os.path.join(iter_dir, "critique.json")
        with open(critique_path, "w", encoding="utf-8") as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

        iteration_duration = time.time() - iteration_start
        iteration_metrics.append(
            {
                "iteration": iteration,
                "duration_seconds": iteration_duration,
                "input_tokens": iteration_input_tokens,
                "output_tokens": iteration_output_tokens,
                "agent_breakdown": agent_breakdown,
            }
        )

        if is_approved(feedback):
            append_run_log("Approved. Stopping iterations.")
            break
        append_run_log("Not approved. Continuing to next iteration.")

    if last_success_md:
        write_text_file(slides_path, last_success_md)
    else:
        write_text_file(slides_path, slides_md)
    elapsed = time.time() - start_time
    typer.echo(f"Done. Final slides at {current_dir}/slides.md")
    typer.echo(f"Elapsed: {elapsed:.2f}s")


    summary_report_path = generate_iteration_summary_report(
        logs_dir=logs_dir,
        mode=mode,
        run_stamp=run_stamp,
        total_iterations=iteration,
        iteration_metrics=iteration_metrics,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_cost=total_cost,
    )
    typer.echo(f"Iteration summary generated at {summary_report_path}")



if __name__ == "__main__":
    app()
