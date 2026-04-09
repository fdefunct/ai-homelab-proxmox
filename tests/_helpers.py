from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys


def load_script_module(path: Path):
    script_dir = str(path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    module_name = f"test_{path.name.replace('-', '_')}_{abs(hash(path))}"
    loader = SourceFileLoader(module_name, str(path))
    spec = spec_from_loader(module_name, loader)
    if spec is None:
        raise RuntimeError(f"Unable to load spec for {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module
