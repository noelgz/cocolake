from __future__ import annotations

import inspect
import json
import logging

from pipeline import llm

logger = logging.getLogger(__name__)


def tool(description: str):
    """Mark a function as a tool the agent can call"""
    def wrapper(func):
        func.tool_description = description
        return func
    return wrapper


class Agent:
    """LLM agent that thinks, acts, and checks results in a loop"""

    def __init__(
        self,
        name: str,
        instructions: str,
        tools: list,
        max_steps: int = 10,
    ):
        self.name = name
        self.instructions = instructions
        self.tools = {f.__name__: f for f in tools}
        self.max_steps = max_steps
        self.last_run_metadata: dict = {}

    async def run(self, task: str, context: list | dict | None = None):
        """Run the loop and return the final result or collected tool data"""
        history: list[str] = []
        collected: list = []
        metadata = {
            "tool_calls": [],
            "errors": [],
            "steps": 0,
            "finished": False,
            "finish_reason": "max_steps",
            "collected_count": 0,
        }
        self.last_run_metadata = metadata

        for step in range(1, self.max_steps + 1):
            metadata["steps"] = step
            prompt = self._build_prompt(task, context, history, len(collected))

            try:
                response = await llm.ask_json(prompt)
            except Exception as exc:
                logger.warning("[%s] LLM failed at step %d: %s", self.name, step, exc)
                metadata["errors"].append({"step": step, "error": str(exc)})
                metadata["finish_reason"] = "llm_error"
                break

            if isinstance(response, list):
                # Real tool results are safer here!
                result = collected if collected else response
                metadata["finished"] = True
                metadata["finish_reason"] = "direct_list"
                metadata["collected_count"] = len(result)
                logger.info("[%s] Done in %d steps (%d items)", self.name, step, len(result))
                return result

            # The agent says it is done
            if response.get("done"):
                # Real tool results are safer here!
                result = collected if collected else response.get("result", [])
                metadata["finished"] = True
                metadata["finish_reason"] = "done_signal"
                metadata["collected_count"] = len(result)
                logger.info("[%s] Done in %d steps (%d items)", self.name, step, len(result))
                return result

            # The agent wants to call a tool
            tool_name = response.get("tool", "")
            tool_args = response.get("args", {})

            if tool_name not in self.tools:
                history.append(f"Step {step}: ERROR — unknown tool '{tool_name}'")
                metadata["errors"].append({"step": step, "error": f"unknown tool '{tool_name}'"})
                continue

            logger.info("[%s] Step %d → %s(%s)", self.name, step, tool_name, _compact(tool_args))

            try:
                result = self.tools[tool_name](**tool_args)
                if inspect.isawaitable(result):
                    result = await result
            except Exception as exc:
                history.append(f"Step {step}: {tool_name} → ERROR: {exc}")
                metadata["errors"].append({"step": step, "error": f"{tool_name}: {exc}"})
                continue

            metadata["tool_calls"].append({
                "step": step,
                "tool": tool_name,
                "args": tool_args,
                "result_count": len(result) if isinstance(result, list) else None,
            })

            # Keep list results together for later
            if isinstance(result, list):
                collected.extend(result)
                titles = [r.get("title", "?")[:70] for r in result[:5] if isinstance(r, dict)]
                summary = f"Returned {len(result)} items: {titles}"
                if len(result) > 5:
                    summary += f" ...and {len(result) - 5} more"
            else:
                summary = str(result)[:400]

            history.append(f"Step {step}: {tool_name}({_compact(tool_args)}) → {summary}")

        metadata["collected_count"] = len(collected)
        logger.warning("[%s] Max steps reached, returning %d collected items", self.name, len(collected))
        return collected


    def _build_prompt(self, task, context, history, collected_count):
        tools_text = "\n".join(
            f"  - {name}({_params(fn)}): {fn.tool_description}"
            for name, fn in self.tools.items()
        )

        parts = [self.instructions, "", "## Available Tools", tools_text]

        if context:
            ctx_json = json.dumps(context, ensure_ascii=False, default=str)
            if len(ctx_json) > 20_000:
                ctx_json = ctx_json[:20_000] + "\n... (truncated)"
            parts += ["", "## Context (input data)", ctx_json]

        if history:
            parts += ["", "## What you've done so far", "\n".join(history)]
            parts.append(f"\nArticles collected so far: {collected_count}")

        parts += [
            "",
            "## Your Task",
            task,
            "",
            "## How to Respond (JSON only, no markdown)",
            'Use a tool:  {"tool": "tool_name", "args": {"param": "value"}}',
            'Finished:    {"done": true, "result": <your final output>}',
        ]
        return "\n".join(parts)


# Small helpers here
def _compact(obj, max_len: int = 120) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str) if isinstance(obj, dict) else str(obj)
    return s if len(s) <= max_len else s[:max_len] + "…"


def _params(func) -> str:
    sig = inspect.signature(func)
    return ", ".join(sig.parameters.keys())
