"""Borna 4 – Antrenarea agentului PPO pentru semaforizarea Pieței Romane.

Exemple:
  python -m romana.control.train --pasi 150000                       # doar Piața Romană
  python -m romana.control.train --coridor --pasi 300000             # piața + 4 intersecții vecine
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

# Vecinii imediați care alimentează piața. Bd. Dacia × Str. Polonă nu face parte din coridor: în OSM, Bd. Dacia
# este acolo sens unic de ieșire din piață (doar banda de autobuz în contrasens), deci intersecția nu trimite
# trafic spre piață; rămâne în simulare, pe programul ei actual.
NEIGHBORS = ["dacia_eminescu", "magheru_enescu", "catargiu_manu", "dacia_victoriei"]


def behaviour_cloning(model, env, plan: list[float], steps_per_env: int, epochs: int = 8) -> dict:
    """Preantrenare prin imitație: politica învață întâi să reproducă un plan fix bun, apoi PPO o rafinează.

    Se colectează (observație, acțiune) cu planul fix rulat în toate mediile paralele, apoi rețeaua politicii
    este antrenată supervizat (entropie încrucișată / −log-probabilitate) pe aceste perechi. Astfel PPO
    pornește de la performanța planului, nu de la o politică aleatoare."""
    import numpy as np
    import torch as th

    obs = env.reset()
    O, A = [], []
    for _ in range(steps_per_env):
        acts = np.array(env.env_method("expert_action", plan))
        O.append(obs.copy())
        A.append(acts.copy())
        obs, _, _, _ = env.step(acts)
    O, A = np.concatenate(O), np.concatenate(A)
    pol = model.policy
    opt = th.optim.Adam(pol.parameters(), lr=1e-3)
    ot, at = th.as_tensor(O, dtype=th.float32), th.as_tensor(A, dtype=th.long)
    for _ in range(epochs):
        perm = th.randperm(len(ot))
        for i in range(0, len(ot), 256):
            idx = perm[i:i + 256]
            loss = -pol.get_distribution(ot[idx]).log_prob(at[idx]).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    with th.no_grad():
        acc = float((pol.get_distribution(ot).mode() == at).all(dim=1).float().mean())
    print(f"[imitație] {len(ot)} perechi, plan {plan}, acuratețe {acc:.3f}")
    return {"plan_verde_s": plan, "perechi": int(len(ot)), "acuratete": round(acc, 3)}


def make_env(scen: list[str], controlled: list[str], seed: int, phases, monitor: str, upstream: bool = False):
    """Fabrică de medii (de nivel superior, ca să poată fi trimisă proceselor SubprocVecEnv)."""
    from stable_baselines3.common.monitor import Monitor

    from romana.control.env import RomanaEnv

    return Monitor(RomanaEnv([Path(s) for s in scen], controlled=controlled, seed=seed, romana_phases=phases,
                             upstream_obs=upstream), filename=monitor)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarii", nargs="*", default=None,
                    help="fișiere .sumocfg pentru antrenare (implicit toate din sumo/scenarios)")
    ap.add_argument("--pasi", type=int, default=150_000, help="pași de decizie (1 pas = 5 s simulate)")
    ap.add_argument("--coridor", action="store_true", help="controlează și cele 4 intersecții vecine care alimentează piața")
    ap.add_argument("--nume", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--toate-fazele", action="store_true",
                    help="agentul poate alege și fazele „fără dozare” (implicit doar fazele planului real)")
    ap.add_argument("--medii", type=int, default=6,
                    help="simulări SUMO în paralel (procese separate); 1 = un singur proces")
    ap.add_argument("--obs-amonte", action="store_true",
                    help="observația și recompensa includ cozile din amonte de intrări (~250 m); observația și "
                         "vehiculele neintroduse")
    ap.add_argument("--bc-plan", default=None,
                    help="preantrenare prin imitație a unui plan fix, ex. „50,40,10” (verde N–S, E–V, pietoni, s)")
    ap.add_argument("--bc-pasi", type=int, default=40_000, help="pași de decizie demonstrați de planul fix")
    ap.add_argument("--gamma", type=float, default=0.98)
    ap.add_argument("--lr", type=float, default=None,
                    help="rata de învățare (implicit 3e-4; la --continua, implicit cea salvată în model)")
    ap.add_argument("--continua", action="store_true",
                    help="continuă antrenarea modelului existent models/ppo_<nume>.zip (pașii se adună)")
    args = ap.parse_args(argv)

    from functools import partial

    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import CheckpointCallback
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

    scen = args.scenarii or sorted(glob.glob(str(ROOT / "sumo" / "scenarios" / "*.sumocfg")))
    controlled = ["romana"] + (NEIGHBORS if args.coridor else [])
    name = args.nume or ("coridor" if args.coridor else "romana")
    out = OUTPUT_DIR / "train" / name
    out.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)

    from romana.control.controllers import fixed_phase_indices

    phases = None if args.toate_fazele else fixed_phase_indices()
    path = MODELS_DIR / f"ppo_{name}.zip"
    prev_steps, prev_min = 0, 0.0
    if args.continua:
        old = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        if old.get("faze_actiuni_romana") != phases or old.get("controlate") != controlled:
            raise SystemExit("Modelul existent are alt spațiu de acțiuni; nu poate fi continuat.")
        prev_steps, prev_min = old["pasi"], old["durata_min"]
    # la continuare, jurnalele de episoade primesc un sufix (cele vechi rămân pentru curba de învățare)
    suffix = f"_de_la_{prev_steps}" if args.continua else ""
    fns = [partial(make_env, scen, controlled, args.seed + 1000 * i + prev_steps, phases,
                   str(out / f"monitor_{i}{suffix}"), args.obs_amonte) for i in range(args.medii)]
    env = SubprocVecEnv(fns) if args.medii > 1 else DummyVecEnv(fns)
    # ~1024 de tranziții pe actualizare, indiferent de numărul de medii (multiplu de 64 → loturi întregi de 128)
    n_steps = -(-1024 // (args.medii * 64)) * 64
    if args.continua:
        # la continuare, --lr (dacă e dat) înlocuiește rata salvată: fine-tuning cu pași mai mici
        lr = {"learning_rate": args.lr, "lr_schedule": lambda _: args.lr} if args.lr is not None else None
        model = PPO.load(str(path), env=env, device="cpu", n_steps=n_steps, custom_objects=lr)
    else:
        model = PPO("MlpPolicy", env, learning_rate=args.lr or 3e-4, n_steps=n_steps, batch_size=128, n_epochs=10,
                    gamma=args.gamma, gae_lambda=0.95, ent_coef=0.01 if not args.bc_plan else 0.003,
                    clip_range=0.2 if not args.bc_plan else 0.1,
                    policy_kwargs={"net_arch": [128, 128]}, seed=args.seed, verbose=1, device="cpu")
    t0 = time.time()
    bc_info = None
    if args.bc_plan and not args.continua:
        bc_info = behaviour_cloning(model, env, [float(x) for x in args.bc_plan.split(",")],
                                    args.bc_pasi // args.medii)
    model.learn(total_timesteps=args.pasi, reset_num_timesteps=not args.continua,
                callback=CheckpointCallback(save_freq=max(1, 25_000 // args.medii), save_path=str(out / "checkpoints"),
                                            name_prefix=name))
    model.save(str(path))
    from romana.control.policy_numpy import export

    export(path)                      # copie NumPy a politicii, rulabilă fără PyTorch
    meta = {"model": path.name, "controlate": controlled, "scenarii": [Path(s).name for s in scen],
            "pasi": int(model.num_timesteps), "durata_min": round(prev_min + (time.time() - t0) / 60, 1),
            "preantrenare_imitatie": bc_info,
            "hiperparametri": {"lr": args.lr if args.lr is not None else model.learning_rate, "n_steps": n_steps, "medii_paralele": args.medii, "batch": 128,
                               "gamma": args.gamma, "ent_coef": float(model.ent_coef),
                               "retea": [128, 128], "delta_t_s": 5, "verde_min_s": 10, "verde_max_s": 90},
            "faze_romana": load_json(ROOT / "sumo" / "net" / "network_info.json")["phase_names"],
            "faze_actiuni_romana": phases, "obs_amonte": args.obs_amonte}
    (MODELS_DIR / f"ppo_{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    env.close()
    print(f"[OK] Model salvat: {path}  ({meta['durata_min']} min)")


if __name__ == "__main__":
    main()
