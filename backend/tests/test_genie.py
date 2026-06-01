"""Unit tests for the Genie integration — no live Databricks calls.

These verify: registry parsing/validation (incl. per-(agent,name) dedup and
description sanitization), the row-extraction logic, the offline fallback, live
tool construction, and ``ask`` against fully-mocked SDK objects that mimic real
behavior — a ``MessageStatus``-like enum (``.value``) and exception-based
failure/timeout (``OperationFailed`` / ``TimeoutError``).
"""
from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# Mirror the SDK: MessageStatus is a plain Enum (NOT a str-mixin).
class _MessageStatus(Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OperationFailed(Exception):
    """Stand-in for databricks.sdk.errors.OperationFailed (matched by class name)."""


# --- registry ---------------------------------------------------------------
def test_registry_parses_valid_json(monkeypatch):
    from app import config
    from app.genie import registry

    cfg = config.get_settings()
    monkeypatch.setattr(
        cfg,
        "GENIE_SPACES",
        '[{"name":"drg_shift","space_id":"01ef","agent":"drg","description":"shift"},'
        '{"name":"appeals_q","space_id":"02ef","agent":"appeals","description":"appeals"}]',
        raising=False,
    )
    spaces = registry.load_genie_spaces()
    assert [s.name for s in spaces] == ["drg_shift", "appeals_q"]
    assert spaces[0].tool_name == "genie_drg_shift"
    assert spaces[1].agent == "appeals"


def test_registry_rejects_bad_entries(monkeypatch):
    from app import config
    from app.genie import registry

    cfg = config.get_settings()
    monkeypatch.setattr(
        cfg,
        "GENIE_SPACES",
        '[{"name":"Bad Name","space_id":"x","description":"d"},'
        '{"name":"ok","description":"no id"},'
        '{"name":"ws","space_id":"   ","description":"whitespace id"},'
        '{"name":"dup","space_id":"1","description":"d"},'
        '{"name":"dup","space_id":"2","description":"d"}]',
        raising=False,
    )
    spaces = registry.load_genie_spaces()
    assert [s.name for s in spaces] == ["dup"]  # only first valid 'dup' survives


def test_registry_allows_same_name_across_agents(monkeypatch):
    from app import config
    from app.genie import registry

    cfg = config.get_settings()
    monkeypatch.setattr(
        cfg,
        "GENIE_SPACES",
        '[{"name":"shift","space_id":"1","agent":"drg","description":"d"},'
        '{"name":"shift","space_id":"2","agent":"data","description":"d"}]',
        raising=False,
    )
    spaces = registry.load_genie_spaces()
    assert {(s.agent, s.name) for s in spaces} == {("drg", "shift"), ("data", "shift")}


def test_registry_sanitizes_description(monkeypatch):
    from app import config
    from app.genie import registry

    cfg = config.get_settings()
    long_desc = "line1\nline2\twith   spaces " + "x" * 500
    spaces_json = json.dumps([{"name": "s", "space_id": "1", "description": long_desc}])
    monkeypatch.setattr(cfg, "GENIE_SPACES", spaces_json, raising=False)
    spaces = registry.load_genie_spaces()
    desc = spaces[0].description
    assert "\n" not in desc and "\t" not in desc
    assert "  " not in desc  # collapsed
    assert len(desc) <= 301  # capped (+ ellipsis)


def test_registry_empty_when_unset(monkeypatch):
    from app import config
    from app.genie import registry

    cfg = config.get_settings()
    monkeypatch.setattr(cfg, "GENIE_SPACES", "", raising=False)
    assert registry.load_genie_spaces() == []


# --- status normalization ---------------------------------------------------
def test_status_str_normalizes_enum():
    from app.genie.client import _status_str

    assert _status_str(_MessageStatus.COMPLETED) == "COMPLETED"
    assert _status_str(_MessageStatus.FAILED) == "FAILED"
    assert _status_str("COMPLETED") == "COMPLETED"
    assert _status_str(None) == ""


# --- row extraction ---------------------------------------------------------
def test_extract_rows_inline():
    from app.genie.client import _extract_rows

    sr = SimpleNamespace(
        manifest=SimpleNamespace(
            schema=SimpleNamespace(
                columns=[SimpleNamespace(name="year"), SimpleNamespace(name="mcc_pct")]
            )
        ),
        result=SimpleNamespace(
            data_array=[["2023", "55"], ["2024", "58"], ["2025", "62"]],
            external_links=None,
        ),
    )
    cols, rows, truncated, external = _extract_rows(sr, max_rows=2)
    assert cols == ["year", "mcc_pct"]
    assert rows == [["2023", "55"], ["2024", "58"]]
    assert truncated is True
    assert external is False


def test_extract_rows_handles_none_data_array():
    from app.genie.client import _extract_rows

    sr = SimpleNamespace(
        manifest=SimpleNamespace(schema=SimpleNamespace(columns=[])),
        result=SimpleNamespace(data_array=None, external_links=["https://signed"]),
    )
    cols, rows, truncated, external = _extract_rows(sr, max_rows=50)
    assert rows == []
    assert external is True  # flagged for the caller


# --- offline fallback + live tools ------------------------------------------
def test_no_tools_without_credentials(monkeypatch):
    from app.genie import tools

    monkeypatch.setattr(tools.get_genie_client(), "available", lambda: False)
    assert tools.genie_tools_for("drg") == []


def test_live_tools_built_and_filtered_by_agent(monkeypatch):
    from app.genie import registry, tools

    monkeypatch.setattr(tools.get_genie_client(), "available", lambda: True)
    fake_spaces = [
        registry.GenieSpace("drg_shift", "01", "shift scope", "drg"),
        registry.GenieSpace("drg_providers", "02", "provider scope", "drg"),
        registry.GenieSpace("taxi", "03", "taxi scope", "data"),
    ]
    monkeypatch.setattr(tools, "load_genie_spaces", lambda: fake_spaces)

    drg_tools = tools.genie_tools_for("drg")
    assert {t.name for t in drg_tools} == {"genie_drg_shift", "genie_drg_providers"}
    # description carries the space scope, and the input schema has `question`
    assert "shift scope" in drg_tools[0].description
    assert "question" in drg_tools[0].args_schema.model_fields

    data_tools = tools.genie_tools_for("data")
    assert {t.name for t in data_tools} == {"genie_taxi"}


def test_drg_builder_falls_back_to_mock_tools(monkeypatch):
    # With Genie unavailable, the DRG subagent must still have its mock tools and
    # a MOCK-labeled data-source note.
    from app.genie import tools
    from app.subagents.drg_agent import build_drg_subagent

    monkeypatch.setattr(tools.get_genie_client(), "available", lambda: False)
    sub = build_drg_subagent()
    names = {t.name for t in sub["tools"]}
    assert {"drg_shift_lookup", "icd_driver_lookup", "provider_utilization_lookup"} <= names
    assert "illustrative mock data" in sub["system_prompt"].lower()


def test_drg_builder_uses_live_note_when_genie(monkeypatch):
    from app.genie import registry, tools
    from app.subagents import drg_agent

    monkeypatch.setattr(tools.get_genie_client(), "available", lambda: True)
    monkeypatch.setattr(
        drg_agent,
        "genie_tools_for",
        lambda agent: tools.genie_tools_for(agent),
    )
    monkeypatch.setattr(
        tools,
        "load_genie_spaces",
        lambda: [registry.GenieSpace("drg_shift", "01", "shift", "drg")],
    )
    sub = drg_agent.build_drg_subagent()
    assert {t.name for t in sub["tools"]} == {"genie_drg_shift"}
    assert "LIVE Databricks Genie" in sub["system_prompt"]
    assert "do not label them as mock" in sub["system_prompt"].lower()


def test_data_subagent_none_without_data_spaces(monkeypatch):
    from app.genie import tools
    from app.subagents.data_agent import build_data_subagent

    monkeypatch.setattr(tools.get_genie_client(), "available", lambda: False)
    assert build_data_subagent() is None


# --- end-to-end ask with a mocked WorkspaceClient ---------------------------
def _fake_workspace(message, query_result=None):
    genie = SimpleNamespace(
        start_conversation_and_wait=lambda space_id, content, timeout=None: message,
        create_message_and_wait=lambda space_id, conv, content, timeout=None: message,
        get_message_attachment_query_result=lambda *a, **k: query_result,
    )
    return SimpleNamespace(genie=genie)


def test_ask_happy_path(monkeypatch):
    from app.genie.client import GenieClient

    query_att = SimpleNamespace(query="SELECT 1", description="counts", statement_id="s1")
    text_att = SimpleNamespace(content="Here is the answer.")
    attachment = SimpleNamespace(attachment_id="a1", query=query_att, text=text_att)
    message = SimpleNamespace(
        conversation_id="c1",
        message_id="m1",
        id="m1",
        status=_MessageStatus.COMPLETED,  # real SDK returns an enum
        attachments=[attachment],
        error=None,
    )
    statement_response = SimpleNamespace(
        manifest=SimpleNamespace(schema=SimpleNamespace(columns=[SimpleNamespace(name="n")])),
        result=SimpleNamespace(data_array=[["42"]], external_links=None),
    )
    query_result = SimpleNamespace(statement_response=statement_response)

    client = GenieClient()
    monkeypatch.setattr(client, "_client", lambda: _fake_workspace(message, query_result))

    result = client.ask("space123", "how many?", space_name="drg_shift")
    assert result.error is None
    assert result.status == "COMPLETED"  # enum normalized to its value
    assert result.sql == "SELECT 1"
    assert result.text == "Here is the answer."
    assert result.columns == ["n"]
    assert result.rows == [["42"]]
    assert result.row_count == 1
    assert result.conversation_id == "c1"
    assert "SELECT 1" in result.to_json()


def test_ask_reports_failed_status_enum(monkeypatch):
    # Defensive path: a terminal-bad status is *returned* (not raised).
    from app.genie.client import GenieClient

    calls = {"attach": 0}
    message = SimpleNamespace(
        conversation_id="c1",
        message_id="m1",
        id="m1",
        status=_MessageStatus.FAILED,
        attachments=[],
        error=SimpleNamespace(error="warehouse unavailable"),
    )
    client = GenieClient()
    monkeypatch.setattr(client, "_client", lambda: _fake_workspace(message))
    monkeypatch.setattr(
        client, "_attach_rows", lambda *a, **k: calls.__setitem__("attach", calls["attach"] + 1)
    )
    result = client.ask("s", "q")
    assert result.status == "FAILED"
    assert result.error and "FAILED" in result.error
    assert "warehouse unavailable" in result.error
    assert calls["attach"] == 0  # never tries to fetch rows for a failed message


def test_ask_classifies_operation_failed(monkeypatch):
    from app.genie.client import GenieClient

    def boom(*a, **k):
        raise OperationFailed("failed to reach COMPLETED, got FAILED: bad query")

    fake_w = SimpleNamespace(genie=SimpleNamespace(start_conversation_and_wait=boom))
    client = GenieClient()
    monkeypatch.setattr(client, "_client", lambda: fake_w)
    result = client.ask("s", "q")
    assert result.status == "FAILED"
    assert result.error and "OperationFailed" in result.error


def test_ask_classifies_timeout(monkeypatch):
    from app.genie.client import GenieClient

    def slow(*a, **k):
        raise TimeoutError("deadline exceeded")

    fake_w = SimpleNamespace(genie=SimpleNamespace(start_conversation_and_wait=slow))
    client = GenieClient()
    monkeypatch.setattr(client, "_client", lambda: fake_w)
    result = client.ask("s", "q")
    assert result.status == "TIMEOUT"
    assert result.error and "did not complete" in result.error


def test_ask_scrubs_secrets_from_errors(monkeypatch):
    from app import config
    from app.genie.client import GenieClient

    cfg = config.get_settings()
    monkeypatch.setattr(cfg, "DATABRICKS_TOKEN", "dapiSECRET", raising=False)
    monkeypatch.setattr(cfg, "DATABRICKS_HOST", "https://secret.host", raising=False)

    def boom(*a, **k):
        raise RuntimeError("auth failed for https://secret.host token dapiSECRET")

    fake_w = SimpleNamespace(genie=SimpleNamespace(start_conversation_and_wait=boom))
    client = GenieClient()
    monkeypatch.setattr(client, "_client", lambda: fake_w)
    result = client.ask("s", "q")
    assert "dapiSECRET" not in (result.error or "")
    assert "secret.host" not in (result.error or "")
    assert "***" in result.error


if __name__ == "__main__":
    import subprocess

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q", __file__]))
