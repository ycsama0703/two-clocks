# -*- coding: utf-8 -*-
"""Can Q-RAG's position encoding be driven standalone, and does the collision
survive all the way to the RoPE output?

Everything so far verified the POSITION VALUE collapsing to 19 integer bins.
What matters for the experiment is whether two chunks at colliding positions
receive an identical positional signal after RoPE. If yes, `relative-only` can
be built without reproducing Q-RAG's training at all -- we encode chunk text
with any embedder and apply this layer on top.
"""
import numpy as np
import torch

from rl.bert_predictor import PositionalRotaryEmbedding


# --- lifted verbatim from envs/text_env.py:RelativePositionProcessor ---------
class RelativePositionProcessor:
    def __init__(self, step_size=20):
        self.step_size = step_size
        self.max_value = int(0.9 * step_size)

    def initialize_positions(self, num_texts):
        return np.linspace(0, self.max_value, num_texts).tolist()

    def update_positions(self, selected_indices, positions):
        n = len(positions)
        result = np.zeros(n, dtype=np.float32)
        cur, start = 0, 0
        for end in sorted(selected_indices) + [n]:
            if end > start:
                result[start:end] = np.linspace(0, self.max_value, end - start) + cur
                start = end
            cur += self.step_size
        return result


DIM = 384          # a GTE-base-sized embedding, halved as q_module does
rope = PositionalRotaryEmbedding(dim=DIM // 2, cache_max_seq_len=8192)
print("PositionalRotaryEmbedding instantiated standalone: OK")

proc = RelativePositionProcessor(step_size=20)

for L in (50, 200, 1000):
    init = proc.initialize_positions(L)          # signature: (selected_indices, positions)
    pos = np.asarray(proc.update_positions([], init), dtype=np.float32)
    # one identical embedding, placed at every position: isolates the positional signal
    base = torch.randn(1, 1, DIM)
    emb = base.repeat(L, 1, 1)
    out = rope.rotate_queries_or_keys(emb, torch.tensor(pos), seq_dim=-3)
    out = out.reshape(L, -1)

    q = pos.astype(np.int32)
    adj_same_bin = q[1:] == q[:-1]
    # identical positional signal == identical output for an identical input
    adj_identical = torch.isclose(out[1:], out[:-1], atol=0, rtol=0).all(dim=1).numpy()

    pred = max(0.0, 1 - 18.0 / (L - 1))
    print()
    print("L = %d" % L)
    print("   distinct integer bins           : %d" % len(np.unique(q)))
    print("   predicted collision 1-18/(L-1)  : %.3f" % pred)
    print("   adjacent in same bin            : %.3f" % adj_same_bin.mean())
    print("   adjacent RoPE output IDENTICAL  : %.3f" % adj_identical.mean())
    print("   same-bin implies identical      : %s"
          % bool((adj_same_bin == adj_identical).all()))

print()
print("=== cross-check: two chunks whose positions differ but share a bin ===")
p1, p2 = 12.1, 12.9
base = torch.randn(1, 1, DIM)
o1 = rope.rotate_queries_or_keys(base, torch.tensor([p1]), seq_dim=-3).reshape(-1)
o2 = rope.rotate_queries_or_keys(base, torch.tensor([p2]), seq_dim=-3).reshape(-1)
print("rho=%.1f vs rho=%.1f  ->  max abs diff = %.3e" % (p1, p2, (o1 - o2).abs().max()))
p3 = 13.1
o3 = rope.rotate_queries_or_keys(base, torch.tensor([p3]), seq_dim=-3).reshape(-1)
print("rho=%.1f vs rho=%.1f  ->  max abs diff = %.3e" % (p1, p3, (o1 - o3).abs().max()))
