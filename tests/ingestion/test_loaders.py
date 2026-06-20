# =============================================================================
# test_loaders.py — behaviour tests for MarkdownLoader, PdfLoader, HtmlLoader.
#
# STRATEGY:
#   - Markdown / HTML are plain text -> write REAL files into tmp_path.
#   - PDF parsing depends on pypdf reading a binary -> MONKEYPATCH the PdfReader
#     the loader imports with a scripted FAKE. Isolates OUR logic from pypdf.
# =============================================================================

import pytest
from ingestion import loaders
from ingestion.loaders import MarkdownLoader, PdfLoader, HtmlLoader
from ingestion.models import Document
from common.errors import IngestionError


# -----------------------------------------------------------------------------
# Helper fakes for the PDF tests
# -----------------------------------------------------------------------------
class _FakePage:
    def __init__(self, text):
        self._t = text

    def extract_text(self):
        return self._t  # may be "" or None


class _FakeReader:
    def __init__(self, pages):
        self.pages = pages


# -----------------------------------------------------------------------------
# Shared base-class behaviour (_validate)
# -----------------------------------------------------------------------------
def test_missing_file_raises(tmp_path):
    with pytest.raises(IngestionError) as ei:
        MarkdownLoader().load(tmp_path / "nope.md")
    assert "not found" in ei.value.message.lower()
    assert ei.value.details["path"] == "nope.md"


def test_directory_is_not_a_file(tmp_path):
    with pytest.raises(IngestionError) as ei:
        MarkdownLoader().load(tmp_path)
    assert ei.value.message == "Path is not a file"


# -----------------------------------------------------------------------------
# MarkdownLoader
# -----------------------------------------------------------------------------
def test_markdown_happy_path(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Title\nbody", encoding="utf-8")
    doc = MarkdownLoader().load(p)
    assert isinstance(doc, Document)
    assert "body" in doc.text
    assert doc.source == "doc.md"
    assert doc.metadata["loader"] == "markdown"


def test_markdown_empty_file_raises(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("   \n  ", encoding="utf-8")
    with pytest.raises(IngestionError) as ei:
        MarkdownLoader().load(p)
    assert ei.value.message == "File is empty"


def test_markdown_non_utf8_raises(tmp_path):
    p = tmp_path / "doc.md"
    p.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(IngestionError):
        MarkdownLoader().load(p)


# -----------------------------------------------------------------------------
# PdfLoader — FAKE reader injected via monkeypatch
# -----------------------------------------------------------------------------
def test_pdf_happy_path_joins_pages_and_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(
        loaders,
        "PdfReader",
        lambda path: _FakeReader(
            [_FakePage("hello"), _FakePage(None), _FakePage("world")]
        ),
    )
    p = tmp_path / "x.pdf"
    p.write_bytes(b"")  # _validate just needs a real file

    doc = PdfLoader().load(p)
    assert "hello" in doc.text
    assert "world" in doc.text
    assert doc.metadata == {"loader": "pdf", "pages": 3}


def test_pdf_all_empty_pages_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(
        loaders,
        "PdfReader",
        lambda path: _FakeReader([_FakePage(""), _FakePage(None)]),
    )
    p = tmp_path / "x.pdf"
    p.write_bytes(b"")

    with pytest.raises(IngestionError) as ei:
        PdfLoader().load(p)
    assert ei.value.message == "File is empty / no extractable text"


def test_pdf_reader_failure_is_wrapped(tmp_path, monkeypatch):
    def _boom(path):
        raise ValueError("boom")

    monkeypatch.setattr(loaders, "PdfReader", _boom)
    p = tmp_path / "x.pdf"
    p.write_bytes(b"")

    with pytest.raises(IngestionError) as ei:
        PdfLoader().load(p)
    assert ei.value.message == "Could not read PDF"
    assert isinstance(ei.value.__cause__, ValueError)


def test_pdf_own_error_not_swallowed(tmp_path, monkeypatch):
    # all-empty pages must surface the EMPTY error, not "Could not read PDF"
    monkeypatch.setattr(
        loaders,
        "PdfReader",
        lambda path: _FakeReader([_FakePage(""), _FakePage("")]),
    )
    p = tmp_path / "x.pdf"
    p.write_bytes(b"")

    with pytest.raises(IngestionError) as ei:
        PdfLoader().load(p)
    assert ei.value.message == "File is empty / no extractable text"


# -----------------------------------------------------------------------------
# HtmlLoader
# -----------------------------------------------------------------------------
def test_html_strips_script_and_style(tmp_path):
    html = (
        "<html><head><title>T</title><style>x{}</style></head>"
        "<body><script>bad()</script><p>real text</p></body></html>"
    )
    p = tmp_path / "page.html"
    p.write_text(html, encoding="utf-8")

    doc = HtmlLoader().load(p)
    assert "real text" in doc.text
    assert "bad()" not in doc.text and "x{}" not in doc.text
    assert doc.metadata["title"] == "T"
    assert doc.metadata["loader"] == "html"


def test_html_no_title_is_none(tmp_path):
    html = "<html><body><p>real text</p></body></html>"
    p = tmp_path / "page.html"
    p.write_text(html, encoding="utf-8")

    doc = HtmlLoader().load(p)
    assert doc.metadata["title"] is None


def test_html_empty_after_strip_raises(tmp_path):
    html = "<html><body><script>only()</script></body></html>"
    p = tmp_path / "page.html"
    p.write_text(html, encoding="utf-8")

    with pytest.raises(IngestionError):
        HtmlLoader().load(p)


def test_html_blank_file_raises(tmp_path):
    p = tmp_path / "page.html"
    p.write_text("   ", encoding="utf-8")

    with pytest.raises(IngestionError) as ei:
        HtmlLoader().load(p)
    assert ei.value.message == "No content exists"
