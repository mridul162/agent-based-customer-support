from streamlit_app.components.chat_message import extract_execution_details


def test_extract_execution_details_from_top_level_payload() -> None:
    response = {
        "agent_name": "faq_agent",
        "tool_used": "retrieve_knowledge_tool",
        "latency_ms": 421.2,
        "ticket_id": "TICKET-001",
    }

    details = extract_execution_details(response)

    assert details["agent_name"] == "faq_agent"
    assert details["tool_used"] == "retrieve_knowledge_tool"
    assert details["latency_ms"] == 421.2
    assert details["ticket_id"] == "TICKET-001"


def test_extract_execution_details_from_nested_payload() -> None:
    response = {
        "execution": {
            "agent": "ticket_agent",
            "tool": "create_ticket_tool",
            "latency": 185.5,
        },
        "ticket_id": "TICKET-002",
    }

    details = extract_execution_details(response)

    assert details["agent_name"] == "ticket_agent"
    assert details["tool_used"] == "create_ticket_tool"
    assert details["latency_ms"] == 185.5
    assert details["ticket_id"] == "TICKET-002"
