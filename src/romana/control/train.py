"""Borna 4 – Antrenarea agentului PPO pentru semaforizarea Pieței Romane.

Exemple:
  python -m romana.control.train --pasi 150000                       # doar Piața Romană
  python -m romana.control.train --coridor --pasi 300000             # piața + 5 intersecții vecine
  python -m romana.control.train --scenarii sumo/scenarios/dimineata_*.sumocfg

Modelul se salvează în models/ppo_<nume>.zip; curba de învățare în outputs/train/.
Algoritm: PPO (Schulman et al., 2017) din Stable-Baselines3 (Raffin et al., 2021).
"""
from __future__ import annotations

import argparse
import glob
import json
import time
from pathlib import Path

from romana.common import MODELS_DIR, OUTPUT_DIR, ROOT, load_json

NEIGHBORS = ["dacia_eminescu", "magheru_enescu", "catargiu_manu", "dacia_victoriei", "dacia_polona"]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarii", nargs="*", default=None,
                    help="fișiere .sumocfg pentru antrenare (implicit toate din sumo/scenarios)")
    ap.add_argument("--pasi", type=int, default=150_000, help="pași de decizie (1 pas = 5 s simulate)")
    ap.add_argument("--coridor", action="store_true", help="controlează și cele 5 intersecții vecine")
    ap.add_argument("--nume", default=None)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)

    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import CheckpointCallback
    from stable_baselines3.common.monitor import Monitor

    from romana.control.env import RomanaEnv

    scen = args.scenarii or sorted(glob.glob(str(ROOT / "sumo" / "scenarios" / "*.sumocfg")))
    controlled = ["romana"] + (NEIGHBORS if args.coridor else [])
    name = args.nume or ("coridor" if args.coridor else "romana")
    out = OUTPUT_DIR / "train" / name
    out.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)

    env = Monitor(RomanaEnv([Path(s) for s in scen], controlled=controlled, seed=args.seed),
                  filename=str(out / "monitor"))
    model = PPO("MlpPolicy", env, learning_rate=3e-4, n_steps=1024, batch_size=128, n_epochs=10,
                gamma=0.98, gae_lambda=0.95, ent_coef=0.01, clip_range=0.2,
                policy_kwargs={"net_arch": [128, 128]}, seed=args.seed, verbose=1, device="cpu")
    t0 = time.time()
    model.learn(total_timesteps=args.pasi,
                callback=CheckpointCallback(save_freq=25_000, save_path=str(out / "checkpoints"), name_prefix=name))
    path = MODELS_DIR / f"ppo_{name}.zip"
    model.save(str(path))
    from romana.control.policy_numpy import export

    export(path)                      # copie NumPy a politicii, rulabilă fără PyTorch
    meta = {"model": path.name, "controlate": controlled, "scenarii": [Path(s).name for s in scen],
            "pasi": args.pasi, "durata_min": round((time.time() - t0) / 60, 1),
            "hiperparametri": {"lr": 3e-4, "n_steps": 1024, "batch": 128, "gamma": 0.98, "ent_coef": 0.01,
                               "retea": [128, 128], "delta_t_s": 5, "verde_min_s": 10, "verde_max_s": 90},
            "faze_romana": load_json(ROOT / "sumo" / "net" / "network_info.json")["phase_names"]}
    (MODELS_DIR / f"ppo_{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    env.close()
    print(f"[OK] Model salvat: {path}  ({meta['durata_min']} min)")


if __name__ == "__main__":
    main()
