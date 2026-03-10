# Figma MCP Skill 🎨

通过 Figma REST API 读取设计稿颜色、结构、节点信息、效果、间距、透明度，支持图片导出的 OpenClaw 技能。

## 目录 (Table of Contents)

- [功能特性](#功能特性)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [安装依赖](#安装依赖)
  - [配置 Token](#配置-token)
  - [方式一：让龙虾帮你部署（推荐）](#方式一让龙虾帮你部署推荐给-openclaw-用户)
  - [方式二：OpenClaw 技能侧边栏](#方式二openclaw-技能侧边栏推荐手动)
  - [方式三：环境变量](#方式三环境变量)
  - [方式四：openclaw.json](#方式四openclawjson)
- [使用方法](#使用方法)
  - [在 OpenClaw 中使用](#在-openclaw-中使用)
  - [Python 调用](#python-调用)
  - [命令行使用](#命令行使用)
- [API 参考](#api-参考)
  - [get_colors](#get_colors)
  - [get_node_structure](#get_node_structure)
  - [export_image](#export_image)
  - [export_image_from_url](#export_image_from_url)
  - [get_effects](#get_effects)
  - [get_opacity](#get_opacity)
  - [get_spacing](#get_spacing)
  - [parse_figma_url](#parse_figma_url)
  - [check_environment](#check_environment)
  - [check_token](#check_token)
- [环境检测](#环境检测)
- [Token 检测与获取](#token-检测与获取)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [许可](#许可)

---

## 功能特性

### 基础功能
- **颜色提取** — 自动提取设计稿中所有 fill、stroke、background 颜色
- **结构读取** — 递归读取节点树，获取元素类型、名称、位置、圆角
- **URL 解析** — 自动从 Figma URL 提取 file ID 和 node ID
- **环境检测** — 检查 Python 版本、curl 可用性、网络连通性
- **Token 验证** — 验证 Figma Personal Access Token 有效性

### v1.1.0 新增功能
- **图片导出** — 导出节点为 PNG/JPG/SVG/PDF，支持 1x/2x/3x/4x 缩放
- **效果识别** — 提取 DROP_SHADOW、INNER_SHADOW、LAYER_BLUR、BACKGROUND_BLUR
- **透明度识别** — 识别所有非 100% 透明度节点
- **间距识别** — 提取 gap、padding、auto-layout spacing、对齐方式

### 跨会话支持
- 无论在哪个 ChatID 都可使用，强制 MCP 方式获取

## 快速开始

### 环境要求

- **Python** 3.10+
- **curl** 系统已安装
- **网络** 能访问 `https://api.figma.com`
- **Figma PAT** Personal Access Token

### 安装依赖

```bash
pip install requests
```

### 配置 Token

#### 方式一：让龙虾帮你部署（推荐给 OpenClaw 用户）

如果你正在使用 OpenClaw，直接把下面这句话发给你的龙虾：

> **请按照这个 SKILL.md 帮我完成 figma-mcp-skill 的安装：**
> **https://github.com/crazyma99/figma-mcp-skill/blob/master/SKILL.md**

龙虾会自动完成：

- Clone 仓库
- Skill 安装部署
- 提示你把 API Key（Figma PAT）发给它
- 将使用方式发送给你
- 修改完成后同步提交到远程仓库

#### 方式二：OpenClaw 技能侧边栏（推荐手动）

在 OpenClaw WebUI 的技能侧边栏找到 `figma-mcp`，输入你的 Figma PAT。

#### 方式三：环境变量

```bash
export FIGMA_PERSONAL_ACCESS_TOKEN="figd_xxxxxxxxxxxxx"
```

#### 方式四：openclaw.json

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "skills": {
    "entries": {
      "figma-mcp": {
        "enabled": true,
        "apiKey": "figd_xxxxxxxxxxxxx"
      }
    }
  }
}
```

## 使用方法

### 在 OpenClaw 中使用

直接在聊天中发送 Figma 链接，并说明需要读取什么内容：

```
读取这个 Figma 链接的图片导出
https://www.figma.com/design/xxx/Title?node-id=0-1
```

### Python 调用

```python
from skills.figma_mcp import (
    get_colors, get_node_structure, parse_figma_url,
    export_image_from_url, get_effects, get_opacity, get_spacing
)

url = "https://www.figma.com/design/xxx/Title?node-id=0-1"

# 读取颜色
colors = get_colors(url)

# 读取结构
structure = get_node_structure(url)

# 导出图片
images = export_image_from_url(url, format="png", scale=2)

# 读取效果
effects = get_effects(url)

# 读取透明度
opacities = get_opacity(url)

# 读取间距
spacings = get_spacing(url)
```

### 命令行使用

```bash
# 运行示例
python example.py

# 环境检测
python -c "from skills.figma_mcp import check_environment; import json; print(json.dumps(check_environment(), indent=2))"
```

## API 参考

### get_colors

从 Figma 设计稿提取所有颜色。

```python
get_colors(url: str, token: Optional[str] = None) -> List[Dict]
```

**返回：** 颜色列表，每项包含 hex、rgba、node、type、path、role

### get_node_structure

获取 Figma 节点结构。

```python
get_node_structure(url: str, token: Optional[str] = None) -> Dict
```

**返回：** 节点字典，包含 name、type、id、children、位置、透明度、圆角

### export_image

导出节点为图片。

```python
export_image(file_id: str, node_ids: str, token=None, format="png", scale=1) -> Dict[str, str]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| file_id | str | Figma 文件 ID |
| node_ids | str | 节点 ID（逗号分隔） |
| format | str | png/jpg/svg/pdf |
| scale | int | 缩放比例 1/2/3/4 |

**返回：** dict，key 为 node ID，value 为图片 URL

### export_image_from_url

从 URL 导出节点为图片。

```python
export_image_from_url(url: str, token=None, format="png", scale=2) -> Dict[str, str]
```

### get_effects

提取节点效果（阴影、模糊）。

```python
get_effects(url: str, token: Optional[str] = None) -> List[Dict]
```

**返回：** 效果列表，每项包含 type、color、offset_x、offset_y、radius 等

### get_opacity

提取非完全不透明节点的透明度。

```python
get_opacity(url: str, token: Optional[str] = None) -> List[Dict]
```

**返回：** 透明度列表，每项包含 node、type、opacity、percent

### get_spacing

提取间距信息（gap、padding、auto-layout）。

```python
get_spacing(url: str, token: Optional[str] = None) -> List[Dict]
```

**返回：** 间距列表，每项包含 gap、padding、layoutMode、对齐方式

### parse_figma_url

从 URL 提取 file ID 和 node ID。

```python
parse_figma_url(url: str) -> Dict[str, str]
```

**返回：** 包含 file_id、node_id、title 的字典

### check_environment

检查运行环境。

### check_token

验证 Figma Token 有效性。

## 环境检测

运行 `check_environment()` 会检测：

| 项目 | 检查内容 |
|------|----------|
| Python | 版本 >= 3.10 |
| curl | 是否可用 |
| 网络 | 能否连接 api.figma.com |
| Token | 环境变量是否设置 |

## Token 检测与获取

### 获取 Figma PAT

1. 访问 https://www.figma.com/developers/api#access-tokens
2. 点击 "Generate new token"
3. 勾选 `file_read` 权限
4. 复制生成的 token（以 `figd_` 开头）

### 验证 Token

```python
from skills.figma_mcp import check_token

result = check_token()
if result["valid"]:
    print(f"Token 有效，用户: {result['user']}")
else:
    print(f"Token 无效: {result['error']}")
```

## 项目结构

```
figma-mcp-skill/
├── SKILL.md          # 技能主文件（<500行，一层引用）
├── skill.yaml        # 技能元数据（v1.1.0）
├── README.md         # 详细文档（含 TOC）
├── __init__.py       # Python 模块实现（含图片导出、效果、透明度、间距）
├── example.py        # 使用示例
├── requirements.txt  # 依赖列表
└── LICENSE           # MIT 许可证
```

## 常见问题

### Q: 为什么不能用 web_fetch 直接抓取 Figma 网页？

A: Figma 网页需要登录才能访问，直接抓取会跳转到登录页。必须使用 Figma REST API + Token 认证。

### Q: Token 无效怎么办？

A: 检查 Token 是否以 `figd_` 开头，是否有 `file_read` 权限，是否已过期。

### Q: 能读取私有设计稿吗？

A: 可以，只要 Token 对应的 Figma 账户有该文件的访问权限。

### Q: 支持哪些节点类型？

A: 支持所有 Figma 节点类型：FRAME、RECTANGLE、TEXT、GROUP、COMPONENT 等。

### Q: 图片导出支持哪些格式？

A: PNG、JPG、SVG、PDF，支持缩放 1x/2x/3x/4x。

### Q: 效果提取支持哪些类型？

A: DROP_SHADOW（投影）、INNER_SHADOW（内阴影）、LAYER_BLUR（图层模糊）、BACKGROUND_BLUR（背景模糊）。

## 许可

MIT License — Created by 亏贼马的强壮大龙虾 🦞
