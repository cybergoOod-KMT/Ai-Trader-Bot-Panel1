from app.api.routes.config import normalize_optional_text, normalize_secret_input
from app.services.openai_client import OpenAIConnectionClient


def test_normalize_secret_input_treats_blank_as_none() -> None:
    assert normalize_secret_input(None) is None
    assert normalize_secret_input("") is None
    assert normalize_secret_input("   ") is None
    assert normalize_secret_input("  abc  ") == "abc"


def test_normalize_optional_text_trims_values() -> None:
    assert normalize_optional_text(None) is None
    assert normalize_optional_text("   ") is None
    assert normalize_optional_text("  gpt-5  ") == "gpt-5"


def test_openai_client_extracts_output_text() -> None:
    client = OpenAIConnectionClient(api_key="test", model="gpt-5")
    payload = {
        "output": [
            {
                "content": [
                    {"type": "output_text", "text": "OK"},
                    {"type": "output_text", "text": "Done"},
                ]
            }
        ]
    }
    assert client._extract_output_text(payload) == "OK\nDone"
