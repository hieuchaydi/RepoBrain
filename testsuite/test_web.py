from __future__ import annotations

import io

import pytest

from repobrain.web import RequestTooLargeError, _MAX_REQUEST_BODY_BYTES, _read_request_fields


def test_read_request_fields_rejects_oversized_body() -> None:
    oversized = _MAX_REQUEST_BODY_BYTES + 1
    environ = {
        "CONTENT_LENGTH": str(oversized),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(b"x" * oversized),
    }
    with pytest.raises(RequestTooLargeError):
        _read_request_fields(environ)


def test_read_request_fields_accepts_small_json_body() -> None:
    body = b'{"query":"hello"}'
    environ = {
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(body),
    }
    assert _read_request_fields(environ) == {"query": "hello"}
