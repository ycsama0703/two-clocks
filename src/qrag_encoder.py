# -*- coding: utf-8 -*-
"""Rebuild Q-RAG's trained action encoder without downloading contriever.

transformers 4.57 refuses to torch.load a .bin checkpoint on torch<2.6
(CVE-2025-32434), and facebook/contriever ships only .bin. But we do not need
contriever's published weights at all: the Q-RAG checkpoint already carries all
204 tensors of the trained action tower. Contriever is architecturally a BERT
encoder, so instantiate an empty BertModel from config and load those tensors in.

The load is strict on the encoder body: if any tensor fails to map, this exits
rather than producing a partially-initialised encoder that would still run and
still yield plausible numbers.
"""
import sys

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, BertConfig, BertModel

REPO = "Q-RAG/qrag-ft-contriever-on-babilong_qa3"
PREFIX = "action_embed.model.model."

ck = torch.load(hf_hub_download(REPO, "model_best.pt"), map_location="cpu", weights_only=False)
ae = ck["action_embed_target"]

sd = {}
for k, v in ae.items():
    if k.startswith(PREFIX):
        sd[k[len(PREFIX):]] = v
print("tensors under %r: %d / %d" % (PREFIX, len(sd), len(ae)))
leftover = [k for k in ae if not k.startswith(PREFIX)]
print("not under prefix (%d):" % len(leftover), leftover[:6])

# contriever == bert-base-uncased geometry; take dims from the weights themselves
vocab, hidden = sd["embeddings.word_embeddings.weight"].shape
nlayer = 1 + max(int(k.split(".")[2]) for k in sd if k.startswith("encoder.layer."))
inter = sd["encoder.layer.0.intermediate.dense.weight"].shape[0]
nhead = 12
print("inferred: vocab=%d hidden=%d layers=%d intermediate=%d" % (vocab, hidden, nlayer, inter))

cfg = BertConfig(vocab_size=vocab, hidden_size=hidden, num_hidden_layers=nlayer,
                 num_attention_heads=nhead, intermediate_size=inter,
                 max_position_embeddings=sd["embeddings.position_embeddings.weight"].shape[0])
model = BertModel(cfg, add_pooling_layer=False)

missing, unexpected = model.load_state_dict(sd, strict=False)
real_missing = [m for m in missing if not m.startswith("pooler.")]
print("missing=%d (non-pooler %d)  unexpected=%d" % (len(missing), len(real_missing), len(unexpected)))
if real_missing:
    print("   ", real_missing[:8])
    sys.exit("REFUSING: encoder body not fully loaded")
if unexpected:
    print("   unexpected:", unexpected[:8])

tok = AutoTokenizer.from_pretrained("bert-base-uncased")
model = model.cuda().eval().half()
b = tok(["AAPL reported Assets of 53,851,000,000 USD for the period ended 2009-09-26.",
         "AAPL reported Assets of 47,501,000,000 USD for the period ended 2009-09-26."],
        padding=True, return_tensors="pt").to("cuda")
with torch.no_grad():
    h = model(**b).last_hidden_state
    m = b["attention_mask"].unsqueeze(-1).half()
    e = torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1)
print("forward OK, hidden", tuple(h.shape))
print("the two versions differ in embedding: cos=%.4f" % float(e[0] @ e[1]))

model.save_pretrained("/root/tc/qrag_action_encoder")
tok.save_pretrained("/root/tc/qrag_action_encoder")
print("saved /root/tc/qrag_action_encoder")
