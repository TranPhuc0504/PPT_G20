"""Tien ich dung chung. Moi duong dan tinh tuong doi tu thu muc goc PPT_G20_T20."""
import json
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DTYPE = np.float64


def load_config(path=None):
    p = Path(path) if path else ROOT / "config.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def set_seed(seed):
    """Dat seed cho moi nguon ngau nhien (hien chua dung ngau nhien, nhung giu de tai lap)."""
    random.seed(seed)
    np.random.seed(seed)


def data_dir():
    d = ROOT / "data"
    d.mkdir(exist_ok=True)
    return d


def results_dir():
    d = ROOT / "results"
    d.mkdir(exist_ok=True)
    return d
