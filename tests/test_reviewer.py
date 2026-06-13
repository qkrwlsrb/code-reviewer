import json
import pytest
from unittest.mock import MagicMock, patch

from code_reviewer.reviewer import (
    _parse_response,
    review_diff,
    ReviewResult,
    ReviewIssue,
    Severity,
)


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_clean_json_no_issues(self):
        text = json.dumps({"summary": "All good", "issues": []})
        result = _parse_response(text)
        assert result.summary == "All good"
        assert result.issues == []

    def test_with_issue(self):
        data = {
            "summary": "Found issues",
            "issues": [{
                "severity": "HIGH",
                "category": "SECURITY",
                "title": "SQL Injection",
                "description": "User input in SQL",
                "suggestion": "Use parameterized queries",
                "file": "app.py",
                "line": 42,
            }],
        }
        result = _parse_response(json.dumps(data))
        assert len(result.issues) == 1
        issue = result.issues[0]
        assert issue.severity == Severity.HIGH
        assert issue.category == "SECURITY"
        assert issue.file == "app.py"
        assert issue.line == 42

    def test_strips_json_markdown_fence(self):
        data = {"summary": "ok", "issues": []}
        text = f"```json\n{json.dumps(data)}\n```"
        result = _parse_response(text)
        assert result.summary == "ok"

    def test_strips_plain_markdown_fence(self):
        data = {"summary": "ok", "issues": []}
        text = f"```\n{json.dumps(data)}\n```"
        result = _parse_response(text)
        assert result.summary == "ok"

    def test_missing_optional_fields_use_defaults(self):
        data = {
            "issues": [{
                "severity": "LOW",
                "category": "QUALITY",
                "title": "x",
                "description": "d",
                "suggestion": "s",
            }]
        }
        result = _parse_response(json.dumps(data))
        assert result.summary == ""
        assert result.issues[0].file == ""
        assert result.issues[0].line == 0

    def test_null_line_coerced_to_zero(self):
        data = {
            "summary": "",
            "issues": [{
                "severity": "INFO",
                "category": "STYLE",
                "title": "t",
                "description": "d",
                "suggestion": "s",
                "file": "foo.py",
                "line": None,
            }],
        }
        result = _parse_response(json.dumps(data))
        assert result.issues[0].line == 0

    def test_multiple_severities(self):
        data = {
            "summary": "mixed",
            "issues": [
                {"severity": "HIGH",   "category": "SECURITY", "title": "a", "description": "", "suggestion": ""},
                {"severity": "MEDIUM", "category": "BUG",      "title": "b", "description": "", "suggestion": ""},
                {"severity": "LOW",    "category": "QUALITY",  "title": "c", "description": "", "suggestion": ""},
                {"severity": "INFO",   "category": "STYLE",    "title": "d", "description": "", "suggestion": ""},
            ],
        }
        result = _parse_response(json.dumps(data))
        severities = [i.severity for i in result.issues]
        assert severities == [Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]


# ---------------------------------------------------------------------------
# review_diff
# ---------------------------------------------------------------------------

def _make_mock_client(response_text: str):
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


class TestReviewDiff:
    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            review_diff("some diff")

    def test_returns_parsed_result(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        payload = {"summary": "Looks good", "issues": []}
        mock_client = _make_mock_client(json.dumps(payload))

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client):
            result = review_diff("diff --git a/foo.py b/foo.py")

        assert result.summary == "Looks good"
        assert result.issues == []
        assert not result.truncated

    def test_truncates_large_diff(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        mock_client = _make_mock_client(json.dumps({"summary": "ok", "issues": []}))
        large_diff = "x" * 120_001

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client):
            result = review_diff(large_diff)

        assert result.truncated
        # Verify that the content actually sent was trimmed
        call_args = mock_client.models.generate_content.call_args
        sent_contents = call_args.kwargs.get("contents") or call_args.args[1]
        assert len(sent_contents.encode("utf-8")) <= 120_000 + 20  # fence overhead

    def test_custom_model_passed_to_api(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        mock_client = _make_mock_client(json.dumps({"summary": "", "issues": []}))

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client):
            review_diff("diff", model="gemini-2.0-flash")

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.0-flash"

    def test_retries_on_429_then_succeeds(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        from google.genai.errors import ClientError

        ok_response = MagicMock()
        ok_response.text = json.dumps({"summary": "ok", "issues": []})

        err = ClientError(429, {"error": {"code": 429, "message": "quota exceeded"}})
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [err, err, ok_response]

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client), \
             patch("code_reviewer.reviewer.time.sleep") as mock_sleep:
            result = review_diff("diff")

        assert result.summary == "ok"
        assert mock_client.models.generate_content.call_count == 3
        assert mock_sleep.call_count == 2
        # Verify backoff values
        assert mock_sleep.call_args_list[0].args[0] == 30
        assert mock_sleep.call_args_list[1].args[0] == 60

    def test_raises_after_max_retries_exceeded(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        from google.genai.errors import ClientError

        err = ClientError(429, {"error": {"code": 429, "message": "quota exceeded"}})
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = err

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client), \
             patch("code_reviewer.reviewer.time.sleep"):
            with pytest.raises(ClientError):
                review_diff("diff")

        # 1 initial + 3 retries = 4 total attempts
        assert mock_client.models.generate_content.call_count == 4

    def test_retries_on_503_then_succeeds(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        from google.genai.errors import ClientError

        ok_response = MagicMock()
        ok_response.text = json.dumps({"summary": "ok", "issues": []})

        err = ClientError(503, {"error": {"code": 503, "message": "unavailable"}})
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [err, ok_response]

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client), \
             patch("code_reviewer.reviewer.time.sleep") as mock_sleep:
            result = review_diff("diff")

        assert result.summary == "ok"
        assert mock_sleep.call_count == 1

    def test_non_retryable_error_not_retried(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        from google.genai.errors import ClientError

        err = ClientError(403, {"error": {"code": 403, "message": "forbidden"}})
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = err

        with patch("code_reviewer.reviewer.genai.Client", return_value=mock_client), \
             patch("code_reviewer.reviewer.time.sleep") as mock_sleep:
            with pytest.raises(ClientError):
                review_diff("diff")

        assert mock_client.models.generate_content.call_count == 1
        mock_sleep.assert_not_called()
