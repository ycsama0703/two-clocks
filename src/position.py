# -*- coding: utf-8 -*-
"""Standalone driver for Q-RAG's relative position encoding.

Q-RAG's positional layer runs without any of its training machinery, so the
`relative-only` arm of the benchmark needs no reproduction of the paper's model:

    emb = your_embedder(chunk_texts)          # any encoder, e.g. GTE-base
    pos = relative_positions(len(chunks), discovered_idx)
    out = apply_positions(rope, emb, pos)

Vendored here so the benchmark survives a reboot (/tmp gets wiped):
    deps/   einops + rotary_embedding_torch, installed with --no-deps (876 KB).
            WITHOUT --no-deps pip pulls the whole CUDA tree (4.6 GB measured)
            and luyao4's disk is at 88%.
    qrag/   snapshot of github.com/griver/Q-RAG for provenance.
"""
import os
import sys

import numpy as np
import torch

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, "deps"), os.path.join(_HERE, "qrag")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rl.bert_predictor import PositionalRotaryEmbedding  # noqa: E402

STEP_SIZE = 20                      # every env config in Q-RAG uses 20
MAX_VALUE = int(0.9 * STEP_SIZE)    # 18


def relative_positions(n, discovered_idx=(), step_size=STEP_SIZE):
    """Verbatim port of envs/text_env.py:RelativePositionProcessor.update_positions.

    Discovered evidence splits [0, n) into segments; within each segment the
    positions are linearly spread over [0, MAX_VALUE], segments are offset by
    step_size. RoPE later truncates these to int32, so a segment holds at most
    MAX_VALUE+1 = 19 distinguishable positions no matter how long it is.
    """
    max_value = int(0.9 * step_size)
    result = np.zeros(n, dtype=np.float32)
    cur, start = 0, 0
    for end in sorted(discovered_idx) + [n]:
        if end > start:
            result[start:end] = np.linspace(0, max_value, end - start) + cur
            start = end
        cur += step_size
    return result


def make_rope(dim, max_seq_len=8192):
    """q_module.py splits the embedding in half before rotating, hence dim // 2."""
    return PositionalRotaryEmbedding(dim=dim // 2, cache_max_seq_len=max_seq_len)


def apply_positions(rope, emb, positions):
    """emb: (L, D) float tensor. positions: (L,) float. Returns (L, D)."""
    if emb.dim() != 2:
        raise ValueError("emb must be (L, D), got %r" % (tuple(emb.shape),))
    x = emb.unsqueeze(1)                                  # (L, 1, D)
    pos = torch.as_tensor(np.asarray(positions), dtype=torch.float32)
    out = rope.rotate_queries_or_keys(x, pos, seq_dim=-3)
    return out.reshape(emb.shape[0], -1)


def collision_rate(L, delta_i=1, max_value=MAX_VALUE):
    """Closed form: 1 - max_value*delta_i/(L-1), verified bit-exact against RoPE."""
    return max(0.0, 1.0 - max_value * delta_i / (L - 1))


if __name__ == "__main__":
    rope = make_rope(384)
    for L in (50, 200, 1000):
        pos = relative_positions(L)
        emb = torch.randn(1, 384).repeat(L, 1)
        out = apply_positions(rope, emb, pos)
        same = torch.isclose(out[1:], out[:-1], atol=0, rtol=0).all(dim=1).float().mean()
        print("L=%-5d bins=%2d  predicted=%.3f  rope-identical=%.3f"
              % (L, len(np.unique(pos.astype(np.int32))), collision_rate(L), same))
