from pathlib import Path
import pytest

from starlight.analysis import compute
from starlight.schema import Schema

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def schema():
    return Schema(ROOT / "REFERENCE_DATA/starlight-iris-2026")


@pytest.fixture(scope="session")
def data(schema):
    return compute(schema)
