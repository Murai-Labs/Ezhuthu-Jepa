"""I-JEPA-style ViT pretraining loop — seam / block / MAE switchable (TASK PA.005).

One loop, one switched variable. The objective is set by config only; the architecture, compute, and
mask *ratio* are identical across all three variants, so the G1 comparison isolates exactly what it
claims (spec §3):

- ``seam_jepa`` — mask a fixed-size token block **centred on the vowel-sign (seam) region**; predict
  the masked tokens' **latent** features from an EMA target encoder (the mechanism under test).
- ``block_jepa`` — mask a same-size token block at a **random location**; same latent target. Only the
  mask *location* differs from ``seam_jepa`` → the clean K1 control.
- ``mae_seam``  — same seam-centred block; predict the masked patches' **pixels** instead of latents.
  Only the *target* differs from ``seam_jepa`` → the K3 latent-vs-pixel ablation.

The masked-token count is a fixed fraction of the grid (``mask_ratio`` × tokens), identical for every
instance and every objective, so "mask ratio held fixed" is exact, not approximate (AGENTS.md §2.4).
Instances with no sign (inherent-'a' forms, ``seam_source == none``) have no seam to hide and are
excluded from pretraining by default — the same exclusion for every arm, so the comparison stays fair.

Backbone: ViT-Tiny/8 (patch 8 on 96 px → 12×12 = 144 tokens), config-swappable to ViT-Small/8
(DEC-0013). Uses ``dtype=`` autocast (bf16) — never the deprecated ``torch_dtype=`` (AGENTS.md §6).

A run writes ``provenance.json`` (five identifiers), ``metrics.json`` (loss/throughput/memory), and
``encoder.pt`` (context-encoder weights + arch) so the frozen probe (PA.003) can load it as
``encoder: jepa``. Progress is printed every ``log_every`` steps: step/total, elapsed, ETA, loss,
throughput, GPU memory (AGENTS.md §4 / Rule 11).
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import time
import zlib
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from ..config import RunConfig, SCHEMA_VERSION
from ..provenance import hash_paths, validate_run_dir, write_provenance

# Imported lazily-at-callsite would hide the hard dependency; PA.005 *is* where torch enters.
import torch
from torch import nn


@dataclass(frozen=True)
class PretrainConfig:
    """All knobs for one pretraining run. Frozen + hashed into provenance.

    The experiment *identity* fields (objective, seed, mask_ratio) are validated by the locked
    :class:`RunConfig` contract (schema 0.1.0); the rest are training hyperparameters recorded for
    reproducibility. Held identical across objectives: everything except ``objective``.
    """

    # --- experiment identity (validated via RunConfig) ---
    objective: str
    seed: int
    mask_ratio: float
    # --- data ---
    index_jsonl: str
    image_dir: str
    exclude_no_sign: bool = True
    limit_instances: int = 0          # 0 = all train instances; >0 caps for a smoke run
    # --- architecture (ViT-Tiny/8 defaults; swap to Small via config) ---
    img_size: int = 96
    patch_size: int = 8
    embed_dim: int = 192
    depth: int = 12
    num_heads: int = 3
    pred_dim: int = 96
    pred_depth: int = 4
    pred_heads: int = 3
    mlp_ratio: float = 4.0
    # --- optimisation ---
    batch_size: int = 128
    max_steps: int = 3000
    lr: float = 1.0e-3
    weight_decay: float = 0.05
    warmup_steps: int = 100
    ema_base: float = 0.996
    ema_final: float = 1.0
    grad_clip: float = 1.0
    # --- runtime ---
    device: str = "cuda"
    amp_dtype: str = "bf16"           # bf16 | fp16 | fp32 (autocast); dtype= policy, never torch_dtype
    log_every: int = 50

    def __post_init__(self) -> None:
        # Reuse the locked contract's validation for the identity fields (objective/seed/mask_ratio).
        RunConfig(
            schema_version=SCHEMA_VERSION,
            objective=self.objective,
            seed=self.seed,
            mask_ratio=self.mask_ratio,
        )
        if self.patch_size <= 0 or self.img_size % self.patch_size != 0:
            raise ValueError(f"img_size {self.img_size} must be divisible by patch_size {self.patch_size}")
        if self.amp_dtype not in ("bf16", "fp16", "fp32"):
            raise ValueError(f"amp_dtype must be bf16|fp16|fp32, got {self.amp_dtype!r}")

    @property
    def grid(self) -> int:
        return self.img_size // self.patch_size

    @property
    def n_tokens(self) -> int:
        return self.grid * self.grid

    @property
    def n_mask(self) -> int:
        """Masked-token count: fixed fraction of the grid, identical for every instance/objective."""
        return max(1, round(self.mask_ratio * self.n_tokens))

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PretrainConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        allowed = {f.name for f in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown pretrain-config key(s): {sorted(unknown)}")
        return cls(**data)


# --------------------------------------------------------------------------------------------------
# Model — a compact ViT (from scratch; no timm dependency) with an I-JEPA context/target/predictor.
# --------------------------------------------------------------------------------------------------

def build_2d_sincos_pos_embed(grid: int, dim: int) -> torch.Tensor:
    """Fixed 2-D sin-cos positional embedding, shape (grid*grid, dim). dim must be divisible by 4."""
    if dim % 4 != 0:
        raise ValueError(f"pos-embed dim must be divisible by 4, got {dim}")
    quarter = dim // 4
    omega = 1.0 / (10000 ** (np.arange(quarter, dtype=np.float64) / quarter))
    coords = np.arange(grid, dtype=np.float64)
    ys, xs = np.meshgrid(coords, coords, indexing="ij")
    out = []
    for pos in (ys.reshape(-1), xs.reshape(-1)):
        ang = np.outer(pos, omega)
        out += [np.sin(ang), np.cos(ang)]
    emb = np.concatenate(out, axis=1)  # (grid*grid, dim)
    return torch.from_numpy(emb).float()


class Block(nn.Module):
    """Pre-norm transformer block (MHSA + MLP)."""

    def __init__(self, dim: int, heads: int, mlp_ratio: float) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.norm2 = nn.LayerNorm(dim)
        hidden = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(nn.Linear(dim, hidden), nn.GELU(), nn.Linear(hidden, dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.norm1(x)
        x = x + self.attn(h, h, h, need_weights=False)[0]
        x = x + self.mlp(self.norm2(x))
        return x


class Transformer(nn.Module):
    def __init__(self, dim: int, depth: int, heads: int, mlp_ratio: float) -> None:
        super().__init__()
        self.blocks = nn.ModuleList(Block(dim, heads, mlp_ratio) for _ in range(depth))
        self.norm = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for blk in self.blocks:
            x = blk(x)
        return self.norm(x)


class ViTEncoder(nn.Module):
    """Patch-embed + transformer. Operates on a chosen subset of tokens (pos embed added by caller)."""

    def __init__(self, cfg: PretrainConfig) -> None:
        super().__init__()
        self.patch_embed = nn.Conv2d(1, cfg.embed_dim, kernel_size=cfg.patch_size, stride=cfg.patch_size)
        self.transformer = Transformer(cfg.embed_dim, cfg.depth, cfg.num_heads, cfg.mlp_ratio)
        self.register_buffer("pos_embed", build_2d_sincos_pos_embed(cfg.grid, cfg.embed_dim), persistent=False)

    def patchify(self, images: torch.Tensor) -> torch.Tensor:
        """(B,1,H,W) -> (B, n_tokens, embed_dim), with pos embed added."""
        x = self.patch_embed(images)                       # (B, D, g, g)
        x = x.flatten(2).transpose(1, 2)                   # (B, n_tokens, D)
        return x + self.pos_embed.unsqueeze(0)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        return self.transformer(tokens)


class Predictor(nn.Module):
    """Narrow transformer predicting targets at masked positions from visible context + mask tokens."""

    def __init__(self, cfg: PretrainConfig, out_dim: int) -> None:
        super().__init__()
        self.embed = nn.Linear(cfg.embed_dim, cfg.pred_dim)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, cfg.pred_dim))
        nn.init.trunc_normal_(self.mask_token, std=0.02)
        self.register_buffer("pos_embed", build_2d_sincos_pos_embed(cfg.grid, cfg.pred_dim), persistent=False)
        self.transformer = Transformer(cfg.pred_dim, cfg.pred_depth, cfg.pred_heads, cfg.mlp_ratio)
        self.head = nn.Linear(cfg.pred_dim, out_dim)

    def forward(self, ctx: torch.Tensor, vis_idx: torch.Tensor, mask_idx: torch.Tensor) -> torch.Tensor:
        b, n_vis, _ = ctx.shape
        n_mask = mask_idx.shape[1]
        pred_dim = self.mask_token.shape[-1]
        ctx = self.embed(ctx) + _gather(self.pos_embed.unsqueeze(0).expand(b, -1, -1), vis_idx)
        mask_tokens = self.mask_token.expand(b, n_mask, pred_dim)
        mask_tokens = mask_tokens + _gather(self.pos_embed.unsqueeze(0).expand(b, -1, -1), mask_idx)
        x = torch.cat([ctx, mask_tokens], dim=1)
        x = self.transformer(x)
        return self.head(x[:, n_vis:])                     # only the masked-position outputs


def _gather(tokens: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
    """Gather tokens (B, N, D) at per-sample indices idx (B, K) -> (B, K, D)."""
    b, _, d = tokens.shape
    return torch.gather(tokens, 1, idx.unsqueeze(-1).expand(b, idx.shape[1], d))


# --------------------------------------------------------------------------------------------------
# Data + masking.
# --------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class _Instance:
    image: np.ndarray          # (H, W) uint8
    seam_center: tuple[int, int] | None   # (token_row, token_col) of the seam-bbox centre, or None


def _seam_token_center(seam_bbox, patch: int) -> tuple[int, int] | None:
    if seam_bbox is None:
        return None
    x0, y0, x1, y1 = seam_bbox
    cx = ((x0 + x1) / 2.0) / patch
    cy = ((y0 + y1) / 2.0) / patch
    return int(cy), int(cx)


def load_train_instances(cfg: PretrainConfig) -> list[_Instance]:
    """Load train-split images (+ seam-token centre) from the augmented index, excluding no-sign forms."""
    image_dir = Path(cfg.image_dir)
    out: list[_Instance] = []
    with Path(cfg.index_jsonl).open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["split"] != "train":
                continue
            if cfg.exclude_no_sign and rec["seam_bbox"] is None:
                continue
            img = np.asarray(Image.open(image_dir / rec["image"]).convert("L"), dtype=np.uint8)
            out.append(_Instance(img, _seam_token_center(rec["seam_bbox"], cfg.patch_size)))
            if cfg.limit_instances and len(out) >= cfg.limit_instances:
                break
    if not out:
        raise RuntimeError("no train instances loaded (check index_jsonl / exclude_no_sign)")
    return out


def _block_shape(n_mask: int, grid: int) -> tuple[int, int]:
    """Near-square token-block dims (th, tw) with th*tw == n_mask, each <= grid."""
    th = max(1, min(grid, int(round(math.sqrt(n_mask)))))
    tw = math.ceil(n_mask / th)
    while th * tw != n_mask:
        if th * tw > n_mask:
            th -= 1
        else:
            tw += 1
        th = max(1, th)
        tw = min(grid, tw)
        if tw >= grid and th * tw < n_mask:
            th += 1
    return th, min(grid, tw)


def _block_top_left(center, th: int, tw: int, grid: int, rng: np.random.Generator, seam: bool):
    """Top-left (row, col) for a th×tw block: seam-centred (clamped) or random."""
    if seam and center is not None:
        r = int(np.clip(center[0] - th // 2, 0, grid - th))
        c = int(np.clip(center[1] - tw // 2, 0, grid - tw))
        return r, c
    r = int(rng.integers(0, grid - th + 1))
    c = int(rng.integers(0, grid - tw + 1))
    return r, c


def _mask_indices_for_batch(batch, cfg: PretrainConfig, seam_centred: bool, rng: np.random.Generator):
    """Return (mask_idx, vis_idx) int arrays of shape (B, n_mask) / (B, n_tokens - n_mask)."""
    grid, n_mask = cfg.grid, cfg.n_mask
    th, tw = _block_shape(n_mask, grid)
    all_tokens = np.arange(cfg.n_tokens)
    mask_rows, vis_rows = [], []
    for inst in batch:
        r, c = _block_top_left(inst.seam_center, th, tw, grid, rng, seam_centred)
        rows = (np.arange(r, r + th)[:, None] * grid + np.arange(c, c + tw)[None, :]).reshape(-1)
        mask = np.zeros(cfg.n_tokens, dtype=bool)
        mask[rows] = True
        mask_rows.append(all_tokens[mask])
        vis_rows.append(all_tokens[~mask])
    return np.stack(mask_rows), np.stack(vis_rows)


# --------------------------------------------------------------------------------------------------
# Training.
# --------------------------------------------------------------------------------------------------

def _amp_dtype(name: str) -> torch.dtype:
    return {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[name]


def _patch_pixels(images: torch.Tensor, mask_idx: torch.Tensor, patch: int, grid: int) -> torch.Tensor:
    """Normalised pixel targets for masked patches: (B, n_mask, patch*patch)."""
    b = images.shape[0]
    x = images.unfold(2, patch, patch).unfold(3, patch, patch)      # (B,1,g,g,p,p)
    x = x.reshape(b, grid * grid, patch * patch)                    # (B, n_tokens, p*p)
    tgt = _gather(x, mask_idx)
    mean = tgt.mean(dim=-1, keepdim=True)
    std = tgt.std(dim=-1, keepdim=True) + 1e-6
    return (tgt - mean) / std


def train(cfg: PretrainConfig, run_dir: Path) -> Path:
    torch.manual_seed(cfg.seed)
    rng = np.random.default_rng(cfg.seed)
    device = torch.device(cfg.device if (cfg.device != "cuda" or torch.cuda.is_available()) else "cpu")
    amp = _amp_dtype(cfg.amp_dtype)
    latent = cfg.objective in ("seam_jepa", "block_jepa")
    seam_centred = cfg.objective in ("seam_jepa", "mae_seam")

    instances = load_train_instances(cfg)
    images = torch.from_numpy(np.stack([i.image for i in instances])).float().div_(255.0).unsqueeze(1)

    context = ViTEncoder(cfg).to(device)
    predictor = Predictor(cfg, out_dim=cfg.embed_dim if latent else cfg.patch_size ** 2).to(device)
    target = copy.deepcopy(context).to(device).requires_grad_(False) if latent else None

    params = list(context.parameters()) + list(predictor.parameters())
    opt = torch.optim.AdamW(params, lr=cfg.lr, weight_decay=cfg.weight_decay, betas=(0.9, 0.95))
    n_params = sum(p.numel() for p in context.parameters())

    print(
        f"[pretrain] objective={cfg.objective} device={device.type} amp={cfg.amp_dtype} "
        f"instances={len(instances)} tokens={cfg.n_tokens} n_mask={cfg.n_mask} "
        f"encoder_params={n_params/1e6:.2f}M steps={cfg.max_steps}",
        flush=True,
    )
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    context.train()
    predictor.train()
    started = time.monotonic()
    running = 0.0
    final_loss = float("nan")
    for step in range(1, cfg.max_steps + 1):
        idx = rng.integers(0, len(instances), cfg.batch_size)
        batch = [instances[i] for i in idx]
        imgs = images[idx].to(device, non_blocking=True)
        mask_np, vis_np = _mask_indices_for_batch(batch, cfg, seam_centred, rng)
        mask_idx = torch.from_numpy(mask_np).to(device)
        vis_idx = torch.from_numpy(vis_np).to(device)

        lr = cfg.lr * min(1.0, step / max(1, cfg.warmup_steps))
        for g in opt.param_groups:
            g["lr"] = lr

        with torch.autocast(device_type=device.type, dtype=amp, enabled=(amp != torch.float32)):
            tokens = context.patchify(imgs)                 # (B, n_tokens, D) with pos
            ctx = context(_gather(tokens, vis_idx))         # encode visible only
            pred = predictor(ctx, vis_idx, mask_idx)        # (B, n_mask, out_dim)
            if latent:
                with torch.no_grad():
                    tgt_tokens = target.patchify(imgs)
                    tgt_all = target(tgt_tokens)
                    tgt = _gather(tgt_all, mask_idx).float()
                loss = nn.functional.smooth_l1_loss(pred.float(), tgt)
            else:
                tgt = _patch_pixels(imgs, mask_idx, cfg.patch_size, cfg.grid)
                loss = nn.functional.mse_loss(pred.float(), tgt)

        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(params, cfg.grad_clip)
        opt.step()

        if latent:
            m = cfg.ema_base + (cfg.ema_final - cfg.ema_base) * (step / cfg.max_steps)
            with torch.no_grad():
                for tp, cp in zip(target.parameters(), context.parameters()):
                    tp.mul_(m).add_(cp.detach(), alpha=1.0 - m)

        running += loss.item()
        final_loss = loss.item()
        if step % cfg.log_every == 0 or step == cfg.max_steps:
            el = time.monotonic() - started
            thru = step * cfg.batch_size / el
            mem = torch.cuda.max_memory_allocated(device) / 1e6 if device.type == "cuda" else 0.0
            print(
                f"[pretrain] step {step}/{cfg.max_steps} loss={running/cfg.log_every if step % cfg.log_every == 0 else final_loss:.4f} "
                f"lr={lr:.2e} {thru:6.0f} img/s mem={mem:6.0f}MB "
                f"elapsed={el:5.1f}s eta={el/step*(cfg.max_steps-step):5.1f}s",
                flush=True,
            )
            running = 0.0

    elapsed = time.monotonic() - started
    peak_mem = torch.cuda.max_memory_allocated(device) / 1e6 if device.type == "cuda" else 0.0

    run_dir.mkdir(parents=True, exist_ok=True)
    write_provenance(
        run_dir,
        config=cfg,
        data_hash=hash_paths([Path(cfg.index_jsonl)]),
        run_id=run_dir.name,
        seed=cfg.seed,
        package_names=["numpy", "pillow", "pyyaml", "torch"],
    )
    torch.save(
        {"arch": _arch_dict(cfg), "context_encoder": context.state_dict()},
        run_dir / "encoder.pt",
    )
    payload = {
        "run_id": run_dir.name,
        "task": "PA.005",
        "objective": cfg.objective,
        "device": device.type,
        "n_train_instances": len(instances),
        "n_tokens": cfg.n_tokens,
        "n_mask": cfg.n_mask,
        "encoder_params_m": round(n_params / 1e6, 3),
        "steps": cfg.max_steps,
        "final_loss": float(final_loss),
        "throughput_img_s": round(cfg.max_steps * cfg.batch_size / elapsed, 1),
        "peak_mem_mb": round(peak_mem, 1),
        "elapsed_s": round(elapsed, 1),
        "encoder_checkpoint": "encoder.pt",
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    validate_run_dir(run_dir)
    print(
        f"[pretrain] done objective={cfg.objective} final_loss={final_loss:.4f} "
        f"throughput={payload['throughput_img_s']} img/s peak_mem={peak_mem:.0f}MB -> {metrics_path}",
        flush=True,
    )
    return metrics_path


def _arch_dict(cfg: PretrainConfig) -> dict:
    return {
        "img_size": cfg.img_size, "patch_size": cfg.patch_size, "embed_dim": cfg.embed_dim,
        "depth": cfg.depth, "num_heads": cfg.num_heads, "mlp_ratio": cfg.mlp_ratio,
    }


# --------------------------------------------------------------------------------------------------
# Probe adapter — lets the frozen PA.003 harness load a trained context encoder (encoder: jepa).
# --------------------------------------------------------------------------------------------------

class JepaEncoder:
    """Frozen context encoder wrapped for the akshara probe: mean-pooled token features."""

    name = "jepa"

    def __init__(self, cfg: PretrainConfig, state_dict: dict, device: str = "cuda") -> None:
        self._dev = torch.device(device if (device != "cuda" or torch.cuda.is_available()) else "cpu")
        self._cfg = cfg
        self._enc = ViTEncoder(cfg).to(self._dev).eval()
        self._enc.load_state_dict(state_dict)
        for p in self._enc.parameters():
            p.requires_grad_(False)

    @torch.no_grad()
    def encode(self, images: np.ndarray) -> np.ndarray:
        feats = []
        bs = 256
        for start in range(0, len(images), bs):
            chunk = images[start:start + bs]
            x = torch.from_numpy(np.stack(chunk)).float().div_(255.0).unsqueeze(1).to(self._dev)
            tokens = self._enc.patchify(x)
            out = self._enc(tokens).mean(dim=1)            # mean-pool tokens -> (b, D)
            feats.append(out.float().cpu().numpy())
        return np.concatenate(feats, axis=0)


def load_probe_encoder(checkpoint: str, device: str = "cuda") -> JepaEncoder:
    """Load a PA.005 ``encoder.pt`` for use as the probe's frozen encoder (PA.003 ``encoder: jepa``)."""
    ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
    arch = ckpt["arch"]
    cfg = PretrainConfig(
        objective="seam_jepa", seed=0, mask_ratio=0.25,
        index_jsonl="_", image_dir="_",
        img_size=arch["img_size"], patch_size=arch["patch_size"], embed_dim=arch["embed_dim"],
        depth=arch["depth"], num_heads=arch["num_heads"], mlp_ratio=arch["mlp_ratio"],
    )
    return JepaEncoder(cfg, ckpt["context_encoder"], device=device)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="I-JEPA-style ViT pretraining (seam/block/MAE).")
    parser.add_argument("--config", type=Path, default=Path("configs/phase1/pretrain.yaml"))
    parser.add_argument("--run-dir", type=Path, default=Path("runs/phaseA-smoke-001"))
    parser.add_argument("--objective", type=str, default=None, help="override objective from config")
    args = parser.parse_args(argv)
    cfg = PretrainConfig.from_yaml(args.config)
    if args.objective:
        cfg = PretrainConfig(**{**asdict(cfg), "objective": args.objective})
    train(cfg, args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
