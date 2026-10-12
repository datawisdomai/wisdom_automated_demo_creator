"""DEMO_REPORT.md — what exists after a run, with links and ids, plus anything skipped."""
from __future__ import annotations

from datetime import datetime, timezone

from . import config
from .manifest import State
from .spec import DemoSpec

STEP_ORDER = ["generate", "validate", "ddl", "load", "validate_snowflake", "rq_check_snowflake", "metrics_check", "docs",
              "publish.connection", "publish.domain", "publish.database", "publish.instructions", "publish.knowledge",
              "publish.metrics", "publish.reviewed_queries", "publish.lookup", "publish.documents", "eval", "health", "app", "chat", "agent"]


def base_url(spec: DemoSpec) -> str:
    dep = config.wisdom_deployment(spec.wisdom.deployment)
    host = dep.host or f"{dep.tenant}.askwisdom.ai"
    return f"https://{host}"


def render(spec: DemoSpec, state: State) -> str:
    w = state.wisdom
    url = base_url(spec)
    lines = [f"# {spec.title} — demo build report", "",
             f"Built {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · demo as-of {spec.as_of} · seed {spec.seed}", ""]
    lines += ["## Where everything is", "",
              f"| Asset | Value |", "|---|---|",
              f"| Snowflake | `{spec.qualified_schema}` ({len(spec.tables)} tables, {len(spec.snowflake.views)} views) |",
              f"| Wisdom deployment / workspace | {spec.wisdom.deployment} / {spec.wisdom.workspace_id} |",
              f"| Domain | {spec.wisdom.domain_name} — `{w.get('domain_id', '—')}` |",
              f"| Live App | {w.get('app_name', spec.live_app.get('name', '—'))} — `{w.get('app_id', 'not created')}` |",
              f"| Follow-up chat | `{w.get('followup_conversation_id', 'not asked')}` |",
              f"| Agent (disabled) | {w.get('agent_name', spec.agent.get('name', '—'))} — `{w.get('agent_id', 'not created')}` |",
              f"| Eval | set `{w.get('eval_set_id', '—')}` · last score {w.get('last_score', '—')} |",
              f"| Domain Health run | job `{w.get('health_job_run_id', 'not triggered')}` (review in the Domain Health tab) |",
              f"| Documents | {len(w.get('uploaded_documents') or [])} uploaded |",
              f"| Instance | {url} |", ""]
    lines += ["## Steps", "", "| Step | Status | When | Notes |", "|---|---|---|---|"]
    for step in STEP_ORDER + [s for s in state.data["steps"] if s not in STEP_ORDER]:
        info = state.data["steps"].get(step)
        if not info:
            continue
        notes = {k: v for k, v in info.items() if k not in ("status", "at")}
        note = ", ".join(f"{k}={str(v)[:60]}" for k, v in list(notes.items())[:4])
        lines.append(f"| {step} | {info.get('status')} | {str(info.get('at', ''))[:16]} | {note} |")
    lines.append("")
    skipped = [s for s in ("app", "chat", "agent", "eval") if not state.data["steps"].get(s)]
    manual = list(spec.manual_steps)
    if skipped or manual:
        lines += ["## Still to do by hand", ""]
        for s in skipped:
            lines.append(f"- `{s}` step has not run (`demo {s} {spec.name} --apply`)")
        for m in manual:
            lines.append(f"- {m.get('kind', 'step')}: {', '.join(f'{k}={v}' for k, v in m.items() if k != 'kind')}")
        lines.append("")
    lines += ["## Control points in the data", ""]
    for cp in spec.control_points:
        lines.append(f"- **{cp.id}** {cp.name}" + (f" (hero: {cp.hero})" if cp.hero else ""))
    lines.append("")
    if spec.chat.get("followup_question"):
        lines += ["## Follow-up question", "", f"> {spec.chat['followup_question']}", ""]
    return "\n".join(lines)
