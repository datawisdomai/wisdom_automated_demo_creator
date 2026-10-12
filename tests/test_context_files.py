from demo_creator.context_files import bootstrap_to_knowledge

MD = """# Domain
## 1. Domain Overview
Some overview text.
## 7. Domain Knowledge
- Loss ratio above 1.0 means the line is unprofitable before expenses.
- Short.
## 8. Business Nuances
1. Always filter cancelled policies out of active-book counts.
## 10. Query Routing Hints
| table | use |
| --- | --- |
Prefer V_CUSTOMER_HEALTH for any renewal risk question.
"""


def test_bootstrap_to_knowledge_takes_only_knowledge_sections():
    entries = bootstrap_to_knowledge(MD)
    assert entries == [
        "Loss ratio above 1.0 means the line is unprofitable before expenses.",
        "Always filter cancelled policies out of active-book counts.",
        "Prefer V_CUSTOMER_HEALTH for any renewal risk question.",
    ]
