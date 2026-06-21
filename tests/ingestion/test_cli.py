# =============================================================================
# test_cli.py — behaviour tests for the ingestion CLI (ingestion.cli).
#
# STRATEGY:
#   - Markdown / HTML are plain text -> write REAL files into tmp_path.
#   - PDFs are skipped here; the CLI surface is fully exercisable with .md/.html.
#   - Assertions match what the source ACTUALLY does (read cli.py first).
# =============================================================================

import json

import pytest

from ingestion.cli import (
    build_loader_registery,
    make_chunker,
    chunk_to_dict,
    process_file,
    run,
    main,
)
from ingestion.loaders import MarkdownLoader, PdfLoader, HtmlLoader
from ingestion.chunkers import FixedSizeChunker, RecursiveChunker
from ingestion.models import Chunk
from common.errors import IngestionError, ChunkingError


# -----------------------------------------------------------------------------
# build_loader_registery
# -----------------------------------------------------------------------------
def test_registry_maps_all_five_extensions_to_right_loaders():
    registry = build_loader_registery()

    assert isinstance(registry[".md"], MarkdownLoader)
    assert isinstance(registry[".markdown"], MarkdownLoader)
    assert isinstance(registry[".pdf"], PdfLoader)
    assert isinstance(registry[".html"], HtmlLoader)
    assert isinstance(registry[".htm"], HtmlLoader)


# -----------------------------------------------------------------------------
# make_chunker
# -----------------------------------------------------------------------------
def test_make_chunker_returns_fixed_and_recursive():
    assert isinstance(make_chunker("fixed", 100, 10), FixedSizeChunker)
    assert isinstance(make_chunker("recursive", 100, 10), RecursiveChunker)


def test_make_chunker_unknown_name_raises_value_error():
    with pytest.raises(ValueError):
        make_chunker("nope", 100, 10)


def test_make_chunker_invalid_size_overlap_raises_chunking_error():
    with pytest.raises(ChunkingError):
        make_chunker("fixed", 10, 99)


# -----------------------------------------------------------------------------
# chunk_to_dict
# -----------------------------------------------------------------------------
def test_chunk_to_dict_has_exactly_four_keys_with_values():
    chunk = Chunk(text="hello", source="doc.md", index=2, metadata={"start": 0, "end": 5})

    d = chunk_to_dict(chunk)

    assert set(d.keys()) == {"text", "source", "index", "metadata"}
    assert d["text"] == "hello"
    assert d["source"] == "doc.md"
    assert d["index"] == 2
    assert d["metadata"] == {"start": 0, "end": 5}


# -----------------------------------------------------------------------------
# process_file
# -----------------------------------------------------------------------------
def test_process_file_dispatches_markdown_and_returns_chunks(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Title\n" + ("word " * 50), encoding="utf-8")

    registry = build_loader_registery()
    chunker = make_chunker("fixed", 30, 5)

    chunks = process_file(p, registry, chunker)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.source == "doc.md" for c in chunks)


def test_process_file_unknown_extension_raises_ingestion_error(tmp_path):
    p = tmp_path / "weird.xyz"
    p.write_text("data", encoding="utf-8")

    registry = build_loader_registery()
    chunker = make_chunker("fixed", 30, 5)

    with pytest.raises(IngestionError):
        process_file(p, registry, chunker)


# -----------------------------------------------------------------------------
# run
# -----------------------------------------------------------------------------
def test_run_writes_valid_jsonl(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.md").write_text("# A\n" + ("alpha " * 40), encoding="utf-8")
    (raw / "b.html").write_text(
        "<html><body><p>" + ("beta " * 40) + "</p></body></html>", encoding="utf-8"
    )
    out = tmp_path / "out" / "chunks.jsonl"

    registry = build_loader_registery()
    chunker = make_chunker("fixed", 30, 5)

    summary = run(str(raw), str(out), chunker, registry)

    assert out.exists()
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == summary["total_chunks"]
    for line in lines:
        obj = json.loads(line)
        assert set(obj.keys()) == {"text", "source", "index", "metadata"}
    assert summary["files_ok"] == 2
    assert summary["files_failed"] == 0


def test_run_resilience_skips_failing_files(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "good.md").write_text("# Good\n" + ("alpha " * 40), encoding="utf-8")
    # Unknown extension -> process_file raises IngestionError -> skipped.
    (raw / "bad.xyz").write_text("nope", encoding="utf-8")
    # Empty markdown -> MarkdownLoader raises IngestionError -> skipped.
    (raw / "empty.md").write_text("   \n  ", encoding="utf-8")
    out = tmp_path / "out.jsonl"

    registry = build_loader_registery()
    chunker = make_chunker("fixed", 30, 5)

    summary = run(str(raw), str(out), chunker, registry)

    assert summary["files_ok"] >= 1
    assert summary["files_failed"] >= 1
    assert summary["total_chunks"] > 0


def test_run_missing_input_dir_raises_chunking_error(tmp_path):
    missing = tmp_path / "does_not_exist"
    out = tmp_path / "out.jsonl"

    registry = build_loader_registery()
    chunker = make_chunker("fixed", 30, 5)

    with pytest.raises(ChunkingError):
        run(str(missing), str(out), chunker, registry)


def test_run_input_is_file_not_dir_raises_chunking_error(tmp_path):
    f = tmp_path / "afile.md"
    f.write_text("# hi\nbody", encoding="utf-8")
    out = tmp_path / "out.jsonl"

    registry = build_loader_registery()
    chunker = make_chunker("fixed", 30, 5)

    with pytest.raises(ChunkingError):
        run(str(f), str(out), chunker, registry)


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
def test_main_returns_zero_on_valid_run(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.md").write_text("# A\n" + ("alpha " * 40), encoding="utf-8")
    out = tmp_path / "processed" / "chunks.jsonl"

    code = main(
        [
            "--input", str(raw),
            "--output", str(out),
            "--chunker", "fixed",
            "--size", "30",
            "--overlap", "5",
        ]
    )

    assert code == 0
    assert out.exists()
    assert len(out.read_text(encoding="utf-8").splitlines()) > 0


def test_main_returns_one_on_bad_chunker_args(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.md").write_text("# A\nbody", encoding="utf-8")
    out = tmp_path / "out.jsonl"

    code = main(
        [
            "--input", str(raw),
            "--output", str(out),
            "--chunker", "fixed",
            "--size", "10",
            "--overlap", "99",
        ]
    )

    assert code == 1
