# RH CLI

RH CLI is a modern command line interface for RunningHub standard model APIs and AI Applications.

You can configure credentials, choose curated models, submit tasks, poll results, download outputs, and script everything directly from your terminal.

## Quick Start

```bash
cd rh-cli
python -m pip install -e ".[test]"
rh auth set-key YOUR_RUNNINGHUB_API_KEY
rh check
```

## Standard Models

```bash
rh model list --type image
rh model info rhart-image-n-pro/text-to-image
rh model run --task text-to-image -p "a cute dog" -o ./dog.png
```

## Image And Video Shortcuts

```bash
rh image -p "a cyberpunk city"
rh image --model 2 -p "a product photo of headphones"
rh video --model 3 -p "a dancer in neon street" --duration 5
rh video --model "Seedance" -p "a realistic travel vlog" --param resolution=1080p
```

## AI Applications

```bash
rh app list --sort HOTTEST --size 5
rh app info https://www.runninghub.cn/ai-detail/1877265245566922800
rh app run 1877265245566922800 \
  --node "52:prompt=a girl dancing" \
  --file "39:image=./photo.jpg" \
  -o ./result.png
```

Use `--json` for machine-readable output in scripts and CI.
