"""Opt-in end-to-end smoke test for a running Docker deployment."""

import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import pytest


BASE_URL = os.environ.get("RNAMINING_WEB_URL")
pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="set RNAMINING_WEB_URL to test a running web deployment",
)
ROOT = Path(__file__).resolve().parents[1]


def request(path, *, data=None, headers=None, timeout=600):
    try:
        response = urllib.request.urlopen(
            urllib.request.Request(
                BASE_URL.rstrip("/") + path,
                data=data,
                headers=headers or {},
            ),
            timeout=timeout,
        )
        return response.status, response.read(), response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers


def multipart(fields, file_name, file_content):
    boundary = "----RNAminingSmokeBoundary"
    parts = []
    for name, value in fields.items():
        parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )
    parts.extend(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="fastaData"; filename="{file_name}"\r\n'.encode(),
            b"Content-Type: text/plain\r\n\r\n",
            file_content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def test_running_web_application_end_to_end():
    status, body, _ = request("/")
    assert status == 200
    assert b"RNAmining" in body

    job_id = uuid.uuid4().hex
    fasta = (ROOT / "tests/fixtures/anolis_regression.fa").read_bytes()
    body, headers = multipart({"exec": job_id}, "sequences.fa", fasta)
    status, response, _ = request("/api/upload.php", data=body, headers=headers)
    assert status == 200, response.decode(errors="replace")
    assert b'"return":"success"' in response

    prediction = urllib.parse.urlencode(
        {
            "exec": job_id,
            "coding_type": "coding_prediction",
            "organismslist": "Anolis_carolinensis",
        }
    ).encode()
    status, response, _ = request(
        "/api/predict.php",
        data=prediction,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert status == 200, response.decode(errors="replace")
    assert b'"return":"success"' in response

    status, response, _ = request(f"/results.php?id={job_id}")
    assert status == 200
    assert b"non-coding" in response
    for name in ("RNAmining.zip", "codings.txt", "noncodings.txt"):
        status, _, headers = request(f"/api/download.php?id={job_id}&file={name}")
        assert status == 200
        assert "attachment" in headers.get("Content-Disposition", "")

    status, _, _ = request("/results.php?id=invalid")
    assert status == 400
    status, _, _ = request(f"/api/download.php?id={'f' * 32}&file=predictions.txt")
    assert status == 404

