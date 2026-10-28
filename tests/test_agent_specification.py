"""generateWorkflowFromPrompt (2026-10 shape) -> createWorkflowAgent input conversion."""
from demo_creator.experiences import specification_to_input


def test_specification_to_input_cleans_deltas_and_defaults():
    gen = {"workflow": {
        "nodes": [
            {"id": "n1", "type": "TRIGGER_CORE", "title": "Schedule", "instruction": {"ops": [{"insert": {"text": "Every Tuesday"}}]},
             "config": {"triggerType": "SCHEDULE", "timing": {"intervalInMins": 10080, "startTime": "2026-01-06T07:00:00", "cronExpression": None, "cronTimezone": None},
                        "domainId": None, "delivery": None, "routeMap": None}, "positionX": 0, "positionY": 0, "handle": None},
            {"id": "n2", "type": "DATA_FETCH", "title": "Fetch", "instruction": {"ops": [{"insert": {"text": "sales"}}, {"insert": {"visualization": {"x": 1}}}]},
             "config": None, "positionX": 100, "positionY": 0},
            {"id": "n3", "type": "CONTROL_IF_ELSE", "title": "Check", "instruction": {"ops": []},
             "config": {"routeMap": [{"condition": {"ops": [{"insert": {"text": "below 94"}}]}, "edgeId": "e3", "branchIndex": 0},
                                     {"condition": {"ops": [{"insert": {"text": " "}}]}, "edgeId": "e4", "branchIndex": 1}]}},
            {"id": "n4", "type": "ACTION", "title": "Send", "instruction": {"ops": [{"insert": {"text": "email"}}]},
             "config": {"delivery": {"type": "EMAIL", "emailConfig": {"toEmailIds": []}, "slackConfig": None}}},
        ],
        "edges": [{"id": "e1", "fromNodeId": "n1", "toNodeId": "n2"}, {"id": "e3", "fromNodeId": "n3", "toNodeId": "n4"}, {"id": "ex", "fromNodeId": "n4", "toNodeId": "ghost"}],
        "canvasAnnotation": {"notes": [{"id": "c1", "text": "note", "positionX": 1, "positionY": 2}]},
    }}
    out = specification_to_input(gen, domain_id="ET_DOMAIN_x", default_email="se@example.com")
    n = {x["id"]: x for x in out["nodes"]}
    assert n["n1"]["config"]["timing"] == {"intervalInMins": 10080, "startTime": "2026-01-06T07:00:00"}
    assert "delivery" not in n["n1"]["config"] and "domainId" not in n["n1"]["config"]
    assert n["n2"]["config"] == {"domainId": "ET_DOMAIN_x"}
    assert n["n2"]["instruction"] == {"ops": [{"insert": {"text": "sales"}}]}
    assert n["n3"]["instruction"]["ops"][0]["insert"]["text"] == "Check"
    assert n["n3"]["config"]["routeMap"] == [{"condition": {"ops": [{"insert": {"text": "below 94"}}]}, "edgeId": "e3", "branchIndex": 0}]
    assert n["n4"]["config"]["delivery"] == {"type": "EMAIL", "emailConfig": {"toEmailIds": ["se@example.com"]}}
    assert [e["id"] for e in out["edges"]] == ["e1", "e3"]
    assert out["canvasAnnotation"]["notes"][0]["text"] == "note"
