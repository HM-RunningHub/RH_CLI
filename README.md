# RH CLI

RH CLI 是面向 RunningHub 的现代命令行工具，覆盖标准模型 API 和 AI 应用。

终端里直接完成配置、模型选择、任务提交、轮询、下载和脚本化输出。

## 安装

开发模式：

```bash
cd rh-cli
python -m pip install -e ".[test]"
```

普通安装：

```bash
cd rh-cli
python -m pip install .
```

## 配置

```bash
rh auth set-key YOUR_RUNNINGHUB_API_KEY
rh check
```

API Key 解析顺序：

1. `--api-key`
2. `RUNNINGHUB_API_KEY`
3. `~/.config/rh/config.toml`，Windows 为 `%APPDATA%\\rh\\config.toml`
4. 兼容读取 `~/.openclaw/openclaw.json`

默认输出目录是 `~/rh-output`，也可以用：

```bash
rh auth set-output-dir ./output
rh --output-dir ./output image -p "a cat"
```

## 标准模型

```bash
rh model list --type image
rh model info rhart-image-n-pro/text-to-image
rh model run --task text-to-image -p "a cute dog" -o ./dog.png
rh model run -e rhart-image-n-pro/edit -p "change background to beach" -i ./photo.png
```

`--param key=value` 可重复传入模型私有参数：

```bash
rh model run -e rhart-video/sparkvideo-2.0/text-to-video \
  -p "A cinematic city flythrough" \
  --param duration=10 \
  --param generateAudio=true
```

## 快捷图片与视频

图片生成内置 5 个精选模型菜单：

```bash
rh image -p "赛博朋克城市"
rh image --model 2 -p "a product photo of headphones" -o ./headphones.png
rh image --model "GPT Image 2" -p "remove the person" -i ./input.png
```

视频生成内置 8 个精选模型菜单：

```bash
rh video -p "猫在阳光花园里奔跑"
rh video --model 3 -p "a dancer in neon street" --duration 5
rh video --model "Seedance" -p "a realistic travel vlog" --param resolution=1080p
```

## AI 应用

```bash
rh app list --sort HOTTEST --size 5
rh app info https://www.runninghub.cn/ai-detail/1877265245566922800
rh app run 1877265245566922800 \
  --node "52:prompt=a girl dancing" \
  --file "39:image=./photo.jpg" \
  -o ./result.png
```

`rh app run` 会自动获取可修改节点、上传本地文件、提交任务、轮询结果并下载所有文件。

## JSON 模式

所有主要命令支持全局 `--json`：

```bash
rh --json check
rh --json model list --task text-to-image
rh --json app list --sort NEWEST
```

生成命令在 JSON 模式下输出稳定结构：

```json
{
  "files": ["./result.png"],
  "texts": [],
  "cost": "0.5",
  "duration": 42,
  "task_id": "123"
}
```

