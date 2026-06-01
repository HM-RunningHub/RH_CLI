# RH CLI

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![RunningHub](https://img.shields.io/badge/Powered%20by-RunningHub-ff6a00.svg)](https://www.runninghub.cn)

> A modern command line interface for [RunningHub](https://www.runninghub.cn): **configure → pick a model → submit → poll → download → script** — all from your terminal.

Run text-to-image, image-to-image, text-to-video, image-to-video, and community AI Applications with a single command, and get result files saved locally. Every command supports `--json` for clean integration with scripts and CI.

```bash
rh image -p "a cyberpunk street at night, cinematic"
# OUTPUT_FILE:/Users/you/rh-output/result.png
```

[中文文档](README.md)

---

## ✨ Features

- **Standard model API** — 78+ endpoints across image / video / audio / 3d / text, with `--task` auto-selection.
- **Curated shortcuts** — `rh image` (5 image models) and `rh video` (8 video models), no endpoint IDs to memorize.
- **AI Application orchestration** — `rh app run` fetches editable nodes, uploads files, submits, polls, and downloads everything.
- **Smart inputs** — local images < 5MB become data URIs, larger files / videos are uploaded, URLs pass through.
- **Robust polling** — automatic retries, circuit breaking, and readable errors for failures / low balance.
- **Script friendly** — global `--json`; API keys never appear in logs or error messages.

---

## 📦 Installation

Requires Python ≥ 3.10.

```bash
python -m pip install .            # normal
python -m pip install -e ".[test]" # development
```

This registers the `rh` command (or use `python -m rh_cli`).

---

## 🚀 Quick Start

```bash
rh auth set-key YOUR_RUNNINGHUB_API_KEY   # get it at runninghub.cn
rh check                                  # verify key and balance
rh image -p "a shiba inu wearing a space helmet, 3D render"
```

---

## ⚙️ Configuration

API key resolution order (first match wins):

| Priority | Source |
|:---:|------|
| 1 | `--api-key` |
| 2 | `RUNNINGHUB_API_KEY` env var |
| 3 | `~/.config/rh/config.toml` (Windows: `%APPDATA%\rh\config.toml`) |
| 4 | `~/.openclaw/openclaw.json` (compatibility) |

Output goes to `~/rh-output` by default. Override globally with `rh auth set-output-dir`, per command with `--output-dir`, or via the `RH_OUTPUT_DIR` env var.

Global options: `--api-key`, `--output-dir`, `--json`, `-v/--verbose`, `--version`.

---

## 🖼️ Standard Models

```bash
rh model list --type image
rh model list --task image-to-video
rh model info rhart-image-n-pro/text-to-image
rh model run -e rhart-image-n-pro/text-to-image -p "a cute dog" -o ./dog.png
rh model run --task text-to-image -p "a cute dog"
rh model run -e rhart-image-n-pro/edit -p "change background to a beach" -i ./photo.png
```

Pass model-specific params (types are coerced per the endpoint definition):

```bash
rh model run -e rhart-video/sparkvideo-2.0/text-to-video \
  -p "A cinematic city flythrough" \
  --param duration=10 \
  --param generateAudio=true
```

---

## ⚡ Image & Video Shortcuts

Without `--model` you get an interactive menu; with `--model` (number or name alias) it is skipped.

| `rh image` | `rh video` |
|------|------|
| 1 全能图片PRO (best overall) | 1 全能视频V3.1 Fast (recommended) |
| 2 全能图片V2 (fastest/cheapest) | 2 全能视频X (Grok) |
| 3 悠船 v7 (Midjourney style) | 3 可灵 v3.0 Pro (natural motion) |
| 4 GPT Image 2 (strong editing) | 4 全能视频V3.1 Pro (cinematic) |
| 5 Seedream v5 (photorealistic) | 5 Vidu Q3 / 6 全能视频S / 7 海螺 / 8 Seedance 2.0 |

```bash
rh image -p "a cyberpunk city"
rh image --model 2 -p "a product photo of headphones" -o ./headphones.png
rh video --model 3 -p "a dancer in neon street" --duration 5
rh video --model "Seedance" -p "a realistic travel vlog" --param resolution=1080p
```

---

## 🧩 AI Applications

```bash
rh app list --sort HOTTEST --size 5
rh app info https://www.runninghub.cn/ai-detail/1877265245566922800
rh app run 1877265245566922800 \
  --node "52:prompt=a girl dancing" \
  --file "39:image=./photo.jpg" \
  -o ./result.png
```

- `--node "nodeId:fieldName=value"` — set a node field (repeatable).
- `--file "nodeId:fieldName=/path"` — upload a local file into a node (repeatable).
- `--instance-type plus` — use a higher-spec instance.

`rh app run` automatically fetches nodes, applies edits, uploads files, submits, polls, and downloads all results.

---

## 🤖 JSON Mode

```bash
rh --json check
rh --json model list --task text-to-image

# grab the output path in a script
path=$(rh --json image --model 1 -p "a cat" | jq -r '.files[0]')
```

Generation commands emit a stable structure:

```json
{
  "files": ["/Users/you/rh-output/result.png"],
  "texts": [],
  "cost": "0.5",
  "duration": 42,
  "task_id": "1899999999999999999"
}
```

Errors exit non-zero with `{ "error": "...", "message": "...", "detail": ... }`.

---

## 🛠️ Development

```bash
python -m pip install -e ".[test]"
pytest
```

---

## 📄 License

Released under the [Apache-2.0](LICENSE) license.

## 🔗 Links

- [RunningHub](https://www.runninghub.cn)
- [Get an API key](https://www.runninghub.cn/enterprise-api/sharedApi)
- [中文文档](README.md)
