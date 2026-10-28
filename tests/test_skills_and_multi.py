"""Domain skills (spec, extractor family, publish step) and several Live Apps / chats / agents per demo."""
from pathlib import Path

import yaml

from demo_creator.spec import load_spec, validate_spec, skill_frontmatter
from demo_creator.context_assets import accept_suggestions, ALL_AGENTS, TEXT_KINDS, asset_output_path
from demo_creator.manifest import State
from demo_creator.publish import Publisher


SKILL = """---
name: kampanjrapport
description: "Use for campaign performance and forecast accuracy by chain and week."
---

1. Resolve chain and week. 2. Query V_KAMPANJRAPPORT. 3. Same grid every time.
"""


_N = [0]


def _demo(tmp_path: Path, raw_extra: dict) -> Path:
    _N[0] += 1
    d = tmp_path / f"sk{_N[0]}"
    d.mkdir()
    (d / "01_snowflake_ddl.sql").write_text("CREATE OR REPLACE TABLE X (A INT);\n")
    (d / "skills").mkdir()
    (d / "skills" / "kampanjrapport.md").write_text(SKILL)
    (d / "demo.yaml").write_text(yaml.safe_dump({
        "name": "sk", "title": "Sk", "as_of": "2026-09-30", "data_start": "2024-10-01", "seed": 7,
        "snowflake": {"database": "sk_poc", "schema": "analytics", "load_order": ["X"]},
        "wisdom": {"connection": {"name": "Snowflake Demo", "create": False}, "skills": [{"file": "skills/kampanjrapport.md"}]},
        **raw_extra,
    }))
    return d


def test_skill_spec_and_frontmatter(tmp_path):
    spec = load_spec(_demo(tmp_path, {}))
    assert [s.name for s in spec.wisdom.skills] == ["kampanjrapport"]
    assert spec.wisdom.skills[0].availability == ["CHAT", "COPILOT", "AGENTS"]
    assert skill_frontmatter(SKILL) == {"name": "kampanjrapport", "description": "Use for campaign performance and forecast accuracy by chain and week."}
    assert not [p for p in validate_spec(spec, stage="design") if "skill" in p]


def test_skill_name_must_match_file(tmp_path):
    d = _demo(tmp_path, {})
    (d / "skills" / "kampanjrapport.md").write_text(SKILL.replace("name: kampanjrapport", "name: Other Name"))
    problems = validate_spec(load_spec(d), stage="design")
    assert any("must equal the file stem" in p for p in problems)


def test_multi_experiences_default_to_legacy_single(tmp_path):
    spec = load_spec(_demo(tmp_path, {"live_app": {"name": "Cockpit"}, "chat": {"followup_question": "Why?"}, "agent": {"name": "Watch"}}))
    assert [a["key"] for a in spec.live_apps] == ["cockpit"] and spec.live_app["name"] == "Cockpit"
    assert [c["key"] for c in spec.chats] == ["followup"] and spec.chat["followup_question"] == "Why?"
    assert [a["key"] for a in spec.agents] == ["watch"]


def test_multi_experiences_lists(tmp_path):
    spec = load_spec(_demo(tmp_path, {
        "live_apps": [{"name": "Cockpit", "prompt": "a.md"}, {"name": "Kampanjrapport", "prompt": "b.md", "key": "kr"}],
        "chats": [{"followup_question": "Why?"}, {"name": "skill", "followup_question": "/kampanjrapport Kronmat 2026-W36"}],
        "agents": [{"name": "Watch"}, {"name": "Kampanjprognos-vakt"}],
    }))
    assert [a["key"] for a in spec.live_apps] == ["cockpit", "kr"]
    assert [c["key"] for c in spec.chats] == ["followup", "skill"]
    assert [a["key"] for a in spec.agents] == ["watch", "kampanjprognos_vakt"]
    assert spec.live_app["name"] == "Cockpit" and spec.agent["name"] == "Watch"


def test_text_asset_kinds(tmp_path):
    spec = load_spec(_demo(tmp_path, {}))
    assert TEXT_KINDS["query_log"] == ".sql" and TEXT_KINDS["report_definition"] == ".txt"
    assert asset_output_path(spec, {"spec": "docs/dbql_export.sql", "kind": "query_log"}).name == "dbql_export.sql"
    assert asset_output_path(spec, {"spec": "docs/glossary.md", "kind": "glossary"}).name == "glossary.pdf"


class _Client:
    def __init__(self, suggestions=(), skills=()):
        self._sugg = list(suggestions)
        self.skills = list(skills)
        self.applied: list[str] = []
        self.created: list[dict] = []
        self.updated: list[dict] = []

    def modeling_suggestions(self, domain_id, *, include_all_statuses=True, job_run_id=None):
        return list(self._sugg)

    def apply_modeling_suggestions(self, domain_id, ids):
        self.applied += ids
        return [{"suggestionId": i, "success": True} for i in ids]

    def list_domain_skills(self, domain_id, *, include_markdown=True):
        return [dict(s) for s in self.skills]

    def create_domain_skill(self, domain_id, md, *, availability=None):
        from demo_creator.spec import skill_frontmatter
        s = {"id": f"SKILL_{len(self.skills) + 1}", "version": 1, "name": skill_frontmatter(md)["name"], "skillMarkdown": md, "isActive": True}
        self.skills.append(s)
        self.created.append(s)
        return s

    def update_domain_skill(self, domain_id, skill_id, version, md, *, availability=None):
        for s in self.skills:
            if s["id"] == skill_id:
                s.update(version=version + 1, skillMarkdown=md)
                self.updated.append(s)
                return s
        raise AssertionError("unknown skill")

    def set_domain_skill_active(self, domain_id, skill_id, is_active):
        return {"id": skill_id, "isActive": is_active}


def test_extractor_skill_suggestions_are_a_family():
    assert "SKILL" in ALL_AGENTS
    c = _Client(suggestions=[
        {"id": "s1", "status": "PENDING", "task": {"type": "UPSERT_SKILL", "upsertSkill": {"name": "kampanjrapport"}}},
        {"id": "s2", "status": "PENDING", "task": {"type": "ADD_COLUMN_DESCRIPTION"}},
    ])
    acc = accept_suggestions(c, "D", ["skills"])
    assert c.applied == ["s1"] and acc["by_family"] == {"skills": 1, "descriptions": 1}


def _publisher(tmp_path, client, apply=True):
    spec = load_spec(_demo(tmp_path, {}))
    state = State(spec.dir / ".state.json", {"steps": {}, "wisdom": {"domain_id": "ET_DOMAIN_1"}, "snowflake": {}})
    pub = Publisher.__new__(Publisher)
    pub.spec, pub.state, pub.client, pub.apply, pub.echo, pub.reports = spec, state, client, apply, False, []
    pub.existing = False
    pub.dep = type("Dep", (), {"name": "test"})()
    pub.workspace_label = "ws"
    return pub


def test_publish_skills_creates_missing_and_keeps_extractor_version(tmp_path):
    c = _Client(skills=[{"id": "SKILL_x", "version": 2, "name": "kampanjrapport", "skillMarkdown": "---\nname: kampanjrapport\ndescription: extractor wording\n---\nbody", "isActive": True}])
    pub = _publisher(tmp_path, c)
    rep = pub.sync_skills()
    assert rep.status == "ok" and not c.created and not c.updated          # the extractor's version is kept
    assert pub.state.wisdom["skills"]["kampanjrapport"]["via"] == "extractor"
    c2 = _Client()
    pub2 = _publisher(tmp_path, c2)
    rep2 = pub2.sync_skills()
    assert rep2.status == "ok" and [s["name"] for s in c2.created] == ["kampanjrapport"]
    assert pub2.state.wisdom["skills"]["kampanjrapport"] == {"id": "SKILL_1", "version": 1, "via": "direct", "file": "skills/kampanjrapport.md"}


def test_publish_skills_flags_dangling_refs(tmp_path):
    c = _Client(skills=[{"id": "SKILL_x", "version": 1, "name": "kampanjrapport", "skillMarkdown": SKILL, "isActive": True,
                         "danglingSchemaRefs": ["DB.S.V_KAMPANJRAPPORT.leverans_fran"]}])
    rep = _publisher(tmp_path, c).sync_skills()
    assert rep.status == "failed" and "stale" in rep.detail


def test_publish_skills_dry_run(tmp_path):
    c = _Client()
    rep = _publisher(tmp_path, c, apply=False).sync_skills()
    assert rep.status == "planned" and not c.created
