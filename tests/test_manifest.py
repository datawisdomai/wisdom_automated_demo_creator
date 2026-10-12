from pathlib import Path

from demo_creator.manifest import State


def test_state_save_merges_with_concurrent_writer(tmp_path: Path):
    a = State.load(tmp_path)
    a.set("wisdom", "domain_id", "D1")
    b = State.load(tmp_path)            # loaded after a's first save
    a.set("wisdom", "app_id", "A1")     # a writes again
    b.mark("eval", "ok", score=0.98)    # b writes without knowing about app_id
    final = State.load(tmp_path)
    assert final.wisdom["domain_id"] == "D1"
    assert final.wisdom["app_id"] == "A1"
    assert final.step("eval")["status"] == "ok"


def test_overwrite_does_not_resurrect_ids(tmp_path: Path):
    a = State.load(tmp_path)
    a.set("wisdom", "domain_id", "D1"); a.set("wisdom", "connection_id", "C1"); a.mark("publish.domain", "ok"); a.mark("load", "ok")
    a.overwrite(sections={"wisdom": {"connection_id": "C1"}}, drop_steps=("publish",))
    final = State.load(tmp_path)
    assert final.wisdom == {"connection_id": "C1"}
    assert "publish.domain" not in final.data["steps"] and final.step_ok("load")
