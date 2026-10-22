import importlib.machinery
import importlib.util
import signal
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "zmclaude"


@pytest.fixture
def z():
    """The zmclaude script, loaded as a fresh module for each test."""
    loader = importlib.machinery.SourceFileLoader("zmclaude", str(SCRIPT))
    spec = importlib.util.spec_from_loader("zmclaude", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.URL, module.USER, module.FROM_NAME = "https://mail.example.com", "jane@example.com", ""
    return module


@pytest.fixture(autouse=True)
def deadline():
    # free looped forever on a 25-hour day; fail such a test instead of hanging CI
    def fail(*_):
        raise TimeoutError("test did not finish in 10 s")
    signal.signal(signal.SIGALRM, fail)
    signal.alarm(10)
    yield
    signal.alarm(0)
