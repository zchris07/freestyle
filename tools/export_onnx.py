"""Export the Beat This! 'small0' checkpoint to models/beat_this_small.onnx (dynamic time axis).

    pip install beat_this onnx onnxruntime onnxscript
    python tools/export_onnx.py

Rotary-embedding caching MUST be disabled before tracing, otherwise the cached
frequencies get baked into the graph as constants and the output is wrong.
Verifies the ONNX output against PyTorch at several lengths (expect ~1e-6).
"""
import numpy as np, onnxruntime as ort, torch
from beat_this.inference import load_model
from rotary_embedding_torch import RotaryEmbedding

m = load_model("small0").eval()
for mod in m.modules():
    if isinstance(mod, RotaryEmbedding):
        mod.cache_if_possible = False

class W(torch.nn.Module):
    def __init__(s, m): super().__init__(); s.m = m
    def forward(s, x):
        o = s.m(x); return o["beat"], o["downbeat"]

w = W(m).eval()
out = "models/beat_this_small.onnx"
torch.onnx.export(w, (torch.randn(1, 1500, 128),), out, input_names=["spect"], output_names=["beat", "downbeat"],
                  dynamic_axes={"spect": {1: "T"}, "beat": {1: "T"}, "downbeat": {1: "T"}}, opset_version=17, dynamo=False)
sess = ort.InferenceSession(out)
for T in (1500, 700, 300):
    x = torch.randn(1, T, 128) * 2
    with torch.no_grad(): rb, rd = w(x)
    ob, od = sess.run(None, {"spect": x.numpy()})
    print(T, np.abs(rb.numpy() - ob).max(), np.abs(rd.numpy() - od).max())
