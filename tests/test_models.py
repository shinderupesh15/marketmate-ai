from types import SimpleNamespace

import pytest
from openai import LengthFinishReasonError

from market_research.models import Models
from market_research.runtime import ServiceError, Usage


@pytest.mark.parametrize("sdk_exception", [True, False])
def test_truncated_output_retries_with_larger_bounded_limit(tmp_path, sdk_exception):
    limits = []

    class LLM:
        def model_copy(self, update):
            limits.append(update["max_tokens"])
            return self

        def with_structured_output(self, *args, **kwargs):
            return self

        def invoke(self, messages):
            if len(limits) == 1 and sdk_exception:
                error = LengthFinishReasonError.__new__(LengthFinishReasonError)
                Exception.__init__(error, "Private source content must never be logged")
                raise error
            raw = SimpleNamespace(
                usage_metadata={},
                response_metadata={"finish_reason": "length" if len(limits) == 1 else "stop"},
            )
            return {"raw": raw, "parsed": None if len(limits) == 1 else "validated"}

    models = Models.__new__(Models)
    models.llm = LLM()
    models.usage = Usage(tmp_path / "usage.sqlite", "test")
    assert models.ask(object, "task", {}) == "validated"
    assert limits == [3000, 6000]
    assert models.usage.counts()["model"] == 2
    assert "Private source" not in str(models.usage.events())


def test_invalid_output_remains_bounded_and_sanitized(tmp_path):
    class LLM:
        def model_copy(self, update):
            return self

        def with_structured_output(self, *args, **kwargs):
            return self

        def invoke(self, messages):
            raise ValueError("private payload")

    models = Models.__new__(Models)
    models.llm = LLM()
    models.usage = Usage(tmp_path / "usage.sqlite", "test")
    with pytest.raises(ServiceError, match="invalid structured response"):
        models.ask(object, "task", {})
    assert models.usage.counts()["model"] == 2
    assert "private payload" not in str(models.usage.events())
