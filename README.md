# RH CLI

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![RunningHub](https://img.shields.io/badge/Powered%20by-RunningHub-ff6a00.svg)](https://www.runninghub.cn)

> 面向 [RunningHub](https://www.runninghub.cn) 的现代命令行工具，在终端里直接完成 **配置 → 选模型 → 提交任务 → 轮询 → 下载 → 脚本化输出** 的全流程。

文生图、图生图、文生视频、图生视频，以及社区里的各种 AI 应用，一条命令就能跑完并把结果文件落到本地。所有命令都支持 `--json`，可以无缝接进脚本、CI 或其它程序。

```bash
rh image -p "雨夜霓虹下的赛博朋克街道，电影质感"
# OUTPUT_FILE:/Users/you/rh-output/result.png
# 花费：¥0.5    耗时：14s
```

---

## ✨ 特性

- **标准模型 API**：78+ 端点，覆盖 image / video / audio / 3d / text，支持按 `--task` 自动选最优端点。
- **精选快捷菜单**：`rh image` 内置 5 个图片模型、`rh video` 内置 8 个视频模型，记不住端点 ID 也能用。
- **AI 应用编排**：`rh app run` 自动拉取可改节点、上传本地文件、提交、轮询、下载全部结果。
- **智能输入处理**：本地图片小于 5MB 自动转 data URI，大文件或视频自动上传，URL 直接透传。
- **稳健轮询**：失败自动重试，连续失败熔断，识别余额不足/任务失败并给出可读错误。
- **脚本友好**：全局 `--json` 输出稳定结构；密钥永不出现在日志或错误信息里。
- **零配置默认值**：结果默认写入 `~/rh-output`，多文件自动追加 `_1`、`_2`。

---

## 📦 安装

需要 Python ≥ 3.10。

```bash
# 普通安装
python -m pip install .

# 开发模式（含测试依赖）
python -m pip install -e ".[test]"
```

安装后会注册 `rh` 命令；也可以用 `python -m rh_cli` 调用。

---

## 🚀 快速开始

```bash
# 1. 设置 API Key（在 https://www.runninghub.cn 获取）
rh auth set-key YOUR_RUNNINGHUB_API_KEY

# 2. 检查连通性和余额
rh check

# 3. 生成第一张图
rh image -p "一只戴着宇航头盔的柴犬，3D 渲染"
```

`rh check` 正常时输出：

```text
RunningHub 已就绪，余额 ¥929906.265，Key 来源：config
```

---

## ⚙️ 配置

### API Key 解析顺序

按以下顺序查找，命中即用：

| 优先级 | 来源 | 说明 |
|:---:|------|------|
| 1 | `--api-key` | 单次命令临时指定，最高优先级 |
| 2 | `RUNNINGHUB_API_KEY` | 环境变量，适合 CI |
| 3 | 配置文件 | `~/.config/rh/config.toml`（Windows：`%APPDATA%\rh\config.toml`） |
| 4 | 兼容读取 | `~/.openclaw/openclaw.json` 里的 RunningHub 配置（如有） |

### 输出目录

默认写入 `~/rh-output`，可全局或单次覆盖：

```bash
rh auth set-output-dir ./output          # 持久化默认目录
rh --output-dir ./out image -p "a cat"   # 单次覆盖
```

也可用环境变量 `RH_OUTPUT_DIR` 指定。

### 全局选项

| 选项 | 作用 |
|------|------|
| `--api-key TEXT` | 临时指定 API Key |
| `--output-dir PATH` | 临时指定输出目录 |
| `--json` | 输出机器可读 JSON |
| `-v, --verbose` | 打印更多调试信息 |
| `--version` | 显示版本 |

---

## 🧠 命令速查

| 命令 | 作用 |
|------|------|
| `rh check` | 校验 Key、查看余额 |
| `rh auth set-key / show / set-output-dir` | 管理 Key 与默认输出目录 |
| `rh model list / info / run` | 标准模型：列表 / 详情 / 运行 |
| `rh image` | 快捷文生图 / 图生图（5 个精选模型） |
| `rh video` | 快捷文生视频 / 图生视频（8 个精选模型） |
| `rh app list / info / run` | AI 应用：浏览 / 查看节点 / 运行 |

---

## 🖼️ 标准模型

```bash
# 浏览端点
rh model list --type image
rh model list --task image-to-video

# 查看某个端点的参数定义
rh model info rhart-image-n-pro/text-to-image

# 按端点运行（文生图）
rh model run -e rhart-image-n-pro/text-to-image -p "a cute dog" -o ./dog.png

# 按任务自动选最优端点
rh model run --task text-to-image -p "a cute dog"

# 图生图（带输入图）
rh model run -e rhart-image-n-pro/edit -p "把背景换成海滩" -i ./photo.png
```

`--param key=value` 可重复，用来传模型私有参数；类型会按端点定义自动转换（INT/FLOAT/BOOLEAN）：

```bash
rh model run -e rhart-video/sparkvideo-2.0/text-to-video \
  -p "A cinematic city flythrough" \
  --param duration=10 \
  --param generateAudio=true
```

> 提示：先用 `rh model info <endpoint>` 查看该端点支持哪些参数及可选值，再用 `--param` 传入。

---

## ⚡ 快捷图片与视频

不想记端点 ID 时，直接用快捷命令。不带 `--model` 会进入交互式菜单；带 `--model`（编号或名称别名均可）则跳过菜单。

### 图片模型菜单（`rh image`）

| # | 模型 | 特点 |
|:---:|------|------|
| 1 | 全能图片PRO | 香蕉 Pro 同款，默认推荐，综合效果最好 |
| 2 | 全能图片V2 | 香蕉 2 同款，最快最便宜 |
| 3 | 悠船 v7 | Midjourney 风格，欧美大片质感 |
| 4 | GPT Image 2 | 语义理解强，改图也很稳 |
| 5 | Seedream v5 | 字节出品，写实照片感超强 |

```bash
rh image -p "赛博朋克城市"                                   # 交互选模型，默认 1
rh image --model 2 -p "a product photo of headphones" -o ./headphones.png
rh image --model "GPT Image 2" -p "remove the person" -i ./input.png
```

### 视频模型菜单（`rh video`）

| # | 模型 | 特点 |
|:---:|------|------|
| 1 | 全能视频V3.1 Fast | 又快又好，性价比之王（推荐） |
| 2 | 全能视频X | Grok 驱动，想象力超强 |
| 3 | 可灵 v3.0 Pro | 运动自然，拍人物首选 |
| 4 | 全能视频V3.1 Pro | 电影感拉满，适合风景大片 |
| 5 | Vidu Q3 Pro | 风格化独特，适合创意短片 |
| 6 | 全能视频S | Sora 同款引擎 |
| 7 | 海螺 Hailuo | 速度快、画面细腻 |
| 8 | Seedance 2.0 | 最长 15 秒 + 自动配音，最高 4K |

```bash
rh video -p "猫在阳光花园里奔跑"
rh video --model 3 -p "a dancer in neon street" --duration 5
rh video --model "Seedance" -p "a realistic travel vlog" --param resolution=1080p
```

---

## 🧩 AI 应用

运行社区里的 AI 应用（webapp）。先列出 / 查看节点，再带参数运行。

```bash
# 浏览应用（RECOMMEND / HOTTEST / NEWEST）
rh app list --sort HOTTEST --size 5

# 查看某个应用的可修改节点（支持 webappId 或完整 URL）
rh app info https://www.runninghub.cn/ai-detail/1877265245566922800

# 运行：用 --node 改文本/参数节点，用 --file 上传本地文件到指定节点
rh app run 1877265245566922800 \
  --node "52:prompt=a girl dancing" \
  --file "39:image=./photo.jpg" \
  -o ./result.png
```

参数格式：

- `--node "nodeId:fieldName=value"` —— 设置某个节点的字段值，可重复。
- `--file "nodeId:fieldName=/path/to/file"` —— 上传本地文件并把返回的文件名写入该节点，可重复。
- `--instance-type plus` —— 使用更高规格实例（默认 `default`）。

`rh app run` 会自动：拉取节点信息 → 应用你的修改 → 上传文件 → 提交任务 → 轮询直到完成 → 下载所有结果文件。

> 用 `rh app info <id>` 先看清楚每个节点的 `Node ID` 和 `Field`，再决定 `--node` / `--file` 怎么填。

---

## 🤖 JSON 模式（脚本 / CI）

所有主要命令都支持全局 `--json`：

```bash
rh --json check
rh --json model list --task text-to-image
rh --json app list --sort NEWEST
```

`rh --json check` 输出：

```json
{
  "status": "ready",
  "key_prefix": "14cf****",
  "key_source": "env",
  "balance": "929906.265",
  "currency": "CNY",
  "coins": "882663",
  "running_tasks": "0",
  "api_type": "SHARED"
}
```

生成类命令（`model run` / `image` / `video` / `app run`）在 JSON 模式下输出统一结构：

```json
{
  "files": ["/Users/you/rh-output/result.png"],
  "texts": [],
  "cost": "0.5",
  "duration": 42,
  "task_id": "1899999999999999999"
}
```

### 在 Shell 里取结果

```bash
# 生成图片并拿到本地路径
path=$(rh --json image --model 1 -p "a cat" | jq -r '.files[0]')
echo "生成完成：$path"
```

---

## 📁 输出与文件命名

- 默认目录：Unix `~/rh-output`，Windows `%USERPROFILE%\rh-output`。
- `-o ./name.png` 指定具体文件名；`-o ./dir/` 指定目录（用默认文件名）。
- 单任务返回多个文件时，自动追加 `_1`、`_2` …
- 下载的视频会自动做一次 MP4 兼容性头部修补，提升各播放器兼容性。

---

## 🚦 错误处理

出错时以非零状态码退出，并打印结构化错误：

```json
{
  "error": "INSUFFICIENT_BALANCE",
  "message": "账户余额不足：...",
  "detail": { "recharge_url": "https://www.runninghub.cn/vip-rights/4" }
}
```

常见错误码：

| 错误码 | 含义 | 处理建议 |
|------|------|------|
| `NO_API_KEY` | 未配置 Key | `rh auth set-key` 或设 `RUNNINGHUB_API_KEY` |
| `AUTH_FAILED` | Key 无效 | 检查 Key 是否正确/被禁用 |
| `INSUFFICIENT_BALANCE` | 余额不足 | 前往充值后重试 |
| `ENDPOINT_NOT_FOUND` | 端点不存在 | 用 `rh model list` 核对端点 ID |
| `INVALID_PARAM` / `INVALID_NODE_ARG` | 参数格式错误 | 检查 `key=value` / `nodeId:field=value` 格式 |
| `TASK_FAILED` / `TASK_TIMEOUT` | 任务失败/超时 | 查看 detail，调整输入后重试 |
| `UPLOAD_FAILED` / `DOWNLOAD_FAILED` | 上传/下载失败 | 检查文件路径与网络 |

---

## ❓ FAQ

**Q：终端里中文 JSON 显示成乱码？**
A：数据本身是正确的 UTF-8（重定向到文件可验证）。Windows 终端如显示乱码，先执行 `chcp 65001` 切到 UTF-8 代码页。

**Q：我的 API Key 会被记录吗？**
A：不会。Key 不会拼进可见 URL，错误信息和日志里的 Key/Token 也会被自动脱敏。

**Q：怎么知道某个模型支持哪些参数？**
A：`rh model info <endpoint>` 查看参数定义，再用 `--param key=value` 传入。

---

## 🛠️ 开发

```bash
python -m pip install -e ".[test]"
pytest
```

项目结构：

```text
src/rh_cli/
├── main.py            # Typer 根命令
├── config.py          # API Key 解析、配置读写
├── http.py            # HTTP 客户端 + 密钥脱敏
├── poll.py            # 任务轮询（重试/熔断）
├── media.py           # 图片/文件上传、data URI
├── output.py          # 结果结构与文件命名
├── model/             # 标准模型：commands / client / payload / menus
├── app/               # AI 应用：commands / client / nodes
└── catalog/           # 端点目录 capabilities.json + 加载器
```

---

## 📄 许可证

本项目基于 [Apache-2.0](LICENSE) 许可证开源。

## 🔗 链接

- [RunningHub 官网](https://www.runninghub.cn)
- [获取 API Key](https://www.runninghub.cn/enterprise-api/sharedApi)
- [充值 / 套餐](https://www.runninghub.cn/vip-rights/4)
- [English README](README_en.md)
