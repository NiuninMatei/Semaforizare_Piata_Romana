"""Politica PPO exportată în NumPy: rularea agentului fără PyTorch (inferență deterministă).

Rețeaua actorului din Stable-Baselines3 (MLP 2 × 128, tanh) are ~20 000 de parametri; exportul
lor în .npz permite rularea agentului pe orice calculator, inclusiv pe automatul unei
intersecții, fără biblioteci de învățare automată. Rezultatul este identic cu
`model.predict(obs, deterministic=True)` (verificat în test la export).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def export(model_zip: Path) -> Path:
    from stable_baselines3 import PPO

    m = PPO.load(str(model_zip), device="cpu")
    pol = m.policy
    lin = [l for l in pol.mlp_extractor.policy_net if hasattr(l, "weight")]
    arrays = {}
    for i, layer in enumerate(lin):
        arrays[f"W{i}"] = layer.weight.detach().numpy()
        arrays[f"b{i}"] = layer.bias.detach().numpy()
    arrays["Wa"] = pol.action_net.weight.detach().numpy()
    arrays["ba"] = pol.action_net.bias.detach().numpy()
    nvec = getattr(m.action_space, "nvec", None)
    arrays["nvec"] = np.array(nvec if nvec is not None else [m.action_space.n])
    out = model_zip.with_suffix(".npz")
    np.savez(out, **arrays)
    # verificare: aceleași acțiuni ca SB3
    pn = NumpyPolicy(out)
    rng = np.random.default_rng(0)
    for _ in range(200):
        o = rng.random(m.observation_space.shape, dtype=np.float32)
        a_sb3, _ = m.predict(o, deterministic=True)
        assert np.array_equal(np.atleast_1d(a_sb3), pn.predict(o)), "export diferit de SB3"
    return out


class NumpyPolicy:
    def __init__(self, npz: Path):
        d = np.load(npz)
        n = len([k for k in d.files if k.startswith("W") and k != "Wa"])
        self.layers = [(d[f"W{i}"], d[f"b{i}"]) for i in range(n)]
        self.Wa, self.ba, self.nvec = d["Wa"], d["ba"], d["nvec"]

    def predict(self, obs: np.ndarray) -> np.ndarray:
        h = np.asarray(obs, dtype=np.float32)
        for W, b in self.layers:
            h = np.tanh(W @ h + b)
        logits = self.Wa @ h + self.ba
        out, k = [], 0
        for n in self.nvec:
            out.append(int(np.argmax(logits[k:k + n])))
            k += n
        return np.array(out)


if __name__ == "__main__":
    import sys

    for p in sys.argv[1:]:
        print("exportat:", export(Path(p)))
