# Schema-Consumer Audit — `RenderConfig` / `FontSpec` (TASK PA.001, DEC-0006)

Schema: `ezhuthu_jepa.data.render.RenderConfig` and `FontSpec` · created 2026-07-01 (multi-font).
Per AGENTS.md §2.2, every field is enumerated with its consumer(s).

## `FontSpec`

| Field | Type | Consumers |
|-------|------|-----------|
| `id` | str | `TamilRenderer`/`render_and_save` (output filename `{akshara}__{id}.png`, manifest `font_id`); `RenderConfig.from_yaml` (duplicate-id check) |
| `path` | str | `TamilRenderer.__init__` (FreeType + HarfBuzz face); `FontSpec.available`; builder data_hash (`hash_paths`) |
| `index` | int | `TamilRenderer.__init__` (face index in a .ttc collection) |

## `RenderConfig`

| Field | Type / constraint | Consumers |
|-------|-------------------|-----------|
| `fonts` | non-empty tuple[FontSpec] | `build_uyirmei` (iterate available fonts); `from_yaml` (parse/validate); provenance config hash |
| `render_px` | int | `TamilRenderer` (FreeType pixel size, HarfBuzz scale, scratch geometry) |
| `output_px` | int | `_crop_pad_resize` (final square side); tests |
| `ink_threshold` | int | `_ink_bbox` |
| `diff_threshold` | int | `_diff_bbox` (ligature seam) |
| `margin_px` | int | `_crop_pad_resize` (crop padding) |

## Invariants asserted by tests

1. `from_yaml` rejects unknown keys, an empty/missing `fonts` list, a font missing `id`/`path`, and
   duplicate font ids (`RenderError`).
2. `RenderConfig` and `FontSpec` are frozen dataclasses → `dataclasses.asdict` is used by
   `provenance.compute_config_hash`, so a config change changes the run's `config_hash`.
3. Rendering is parametrized over available fonts; absent fonts skip individually.

## Change from the single-font PA.001 draft

`font_path: str` + `font_index: int` were **replaced** by `fonts: tuple[FontSpec]`. No consumer of
the old fields remains (the whole renderer + builder + tests + `render.yaml` were updated in the same
change; `grep -rn "font_path" src tests configs` is empty). Motivation: DEC-0006 multi-font.
