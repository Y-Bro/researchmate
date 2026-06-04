import pathlib
import sys

# Make `src/` importable as the source root (so `import common.config` works).
sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

# Tests must not load or depend on the real .env — they set every env var
# explicitly via monkeypatch. Neutralise load_dotenv before config imports it.
import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *args, **kwargs: None
