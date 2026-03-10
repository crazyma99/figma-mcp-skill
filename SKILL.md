---
name: figma-mcp
description: Figma MCP 读取技能 - 通过 Figma REST API 读取设计稿颜色、结构、节点信息、效果、间距、透明度，支持图片导出和 URL 自动解析
metadata:
  openclaw:
    emoji: "🎨"
    requires:
      config: ["skills.entries.figma-mcp.apiKey"]
    primaryEnv: "FIGMA_PERSONAL_ACCESS_TOKEN"
---

# Figma MCP 读取技能 (Figma MCP Reader)

✅ **已验证可用** (2026-03-10) - 颜色、结构、效果、间距、透明度、图片导出

通过 Figma REST API 读取设计稿内容，自动从 URL 提取 file ID 和 node ID，支持跨会话使用。

## 目录

- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [API 参数](#api-参数)
- [配置](#配置)
- [参考文件](#参考文件)

## 快速开始

### 环境要求

- **Python 版本：** 3.10+
- **curl：** 系统已安装
- **网络：** 需能访问 `https://api.figma.com`
- **Figma PAT：** 需要 Personal Access Token

### 配置 Token

#### 方式一：让龙虾帮你部署（推荐给 OpenClaw 用户）

如果你正在使用 OpenClaw，直接把下面这句话发给你的龙虾：

> **请按照这个 SKILL.md 帮我完成 figma-mcp-skill 的安装：**
> **https://github.com/crazyma99/figma-mcp-skill/blob/master/SKILL.md**

龙虾会自动完成：Clone 仓库 → Skill 安装部署 → 提示输入 API Key（Figma PAT）→ 将使用方式发送给你 → 同步提交到远程仓库。

#### 方式二：OpenClaw 技能侧边栏

在 OpenClaw WebUI 的技能侧边栏配置：

| 字段 | 说明 |
|------|------|
| **PAT** | Figma Personal Access Token |

#### 方式三：环境变量

```bash
export FIGMA_PERSONAL_ACCESS_TOKEN="figd_xxxxxxxxxxxxx"
```

### 读取颜色

```python
from skills.figma_mcp import get_colors

url = "https://www.figma.com/design/H895GidT9BjHSQ2mBfIjxl/Untitled?node-id=0-1"
colors = get_colors(url)
for c in colors:
    print(f"{c['hex']} - {c['node']}")
```

### 读取节点结构

```python
from skills.figma_mcp import get_node_structure

structure = get_node_structure(url)
print(f"节点: {structure['name']}, 子元素: {len(structure['children'])}")
```

### 导出图片

```python
from skills.figma_mcp import export_image_from_url

url = "https://www.figma.com/design/xxx/Title?node-id=0-1"
images = export_image_from_url(url, format="png", scale=2)
for node_id, img_url in images.items():
    print(f"{node_id}: {img_url}")
```

### 读取效果（阴影/模糊）

```python
from skills.figma_mcp import get_effects

effects = get_effects(url)
for e in effects:
    print(f"{e['node']} - {e['type']}: {e.get('color', 'N/A')}")
```

### 读取透明度

```python
from skills.figma_mcp import get_opacity

opacities = get_opacity(url)
for o in opacities:
    print(f"{o['node']}: {o['percent']}")
```

### 读取间距（gap/padding）

```python
from skills.figma_mcp import get_spacing

spacings = get_spacing(url)
for s in spacings:
    if 'gap' in s:
        print(f"{s['node']}: gap={s['gap']}")
    if 'padding' in s:
        print(f"{s['node']}: padding={s['padding']}")
```

## 核心功能

### 1. 颜色提取 (`get_colors`)
- 自动提取所有 fill、stroke、background 颜色
- 输出 HEX 和 RGBA 格式
- 去重并记录出现位置
- 返回 role 字段（fill/stroke/background）

### 2. 结构读取 (`get_node_structure`)
- 递归遍历节点树
- 获取元素类型、名称、位置 (x, y, width, height)
- 包含透明度、圆角信息
- 支持按 node-id 定位

### 3. 图片导出 (`export_image` / `export_image_from_url`)
- 导出任意节点为 PNG/JPG/SVG/PDF
- 支持缩放比例 1x/2x/3x/4x
- 返回可直接访问的图片 URL
- 支持批量导出多个节点

### 4. 效果提取 (`get_effects`)
- DROP_SHADOW (投影阴影)
- INNER_SHADOW (内阴影)
- LAYER_BLUR (图层模糊)
- BACKGROUND_BLUR (背景模糊)
- 包含颜色、偏移、半径、扩散信息

### 5. 透明度识别 (`get_opacity`)
- 识别所有非 100% 透明度节点
- 返回 opacity 值和百分比
- 递归遍历所有子节点

### 6. 间距识别 (`get_spacing`)
- gap (auto-layout itemSpacing)
- padding (top/right/bottom/left)
- counterAxisSpacing
- layoutMode (HORIZONTAL/VERTICAL)
- 对齐方式 (primaryAxisAlign, counterAxisAlign)

### 7. URL 自动解析 (`parse_figma_url`)
- 从 Figma URL 自动提取 file ID
- 自动提取 node-id 参数
- 支持多种 URL 格式

### 8. 环境检测
- Python 版本检查
- curl 可用性检查
- 网络连通性检测
- Token 有效性验证

## API 参数

### get_colors(url, token=None)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma 设计稿 URL |
| token | str | None | PAT（None 时读取环境变量） |

**返回：** `list[dict]` — 颜色列表，每项包含 hex、rgba、node、type、path、role

### get_node_structure(url, token=None)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma 设计稿 URL |
| token | str | None | PAT（None 时读取环境变量） |

**返回：** `dict` — 节点结构，包含 name、type、id、children、位置、透明度、圆角

### export_image(file_id, node_ids, token=None, format="png", scale=1)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| file_id | str | 必填 | Figma 文件 ID |
| node_ids | str | 必填 | 节点 ID（逗号分隔） |
| token | str | None | PAT |
| format | str | "png" | 图片格式 (png/jpg/svg/pdf) |
| scale | int | 1 | 缩放比例 (1/2/3/4) |

**返回：** `dict` — key 为 node ID，value 为图片 URL

### export_image_from_url(url, token=None, format="png", scale=2)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma 设计稿 URL |
| token | str | None | PAT |
| format | str | "png" | 图片格式 |
| scale | int | 2 | 缩放比例 |

**返回：** `dict` — 导出结果

### get_effects(url, token=None)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma URL |
| token | str | None | PAT |

**返回：** `list[dict]` — 效果列表，每项包含 type、color、offset、radius 等

### get_opacity(url, token=None)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma URL |
| token | str | None | PAT |

**返回：** `list[dict]` — 透明度列表，每项包含 node、opacity、percent

### get_spacing(url, token=None)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma URL |
| token | str | None | PAT |

**返回：** `list[dict]` — 间距列表，包含 gap、padding、layoutMode 等

### parse_figma_url(url)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma URL |

**返回：** `dict` — 包含 file_id、node_id、title

### check_environment()

检查运行环境，返回 Python 版本、curl 可用性、网络状态。

### check_token(token=None)

验证 Figma Token 有效性，返回用户信息和权限。

## 配置

### OpenClaw 配置

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

### 环境变量

| 变量名 | 说明 |
|--------|------|
| `FIGMA_PERSONAL_ACCESS_TOKEN` | Figma Personal Access Token |

### 获取 Token

1. 访问 https://www.figma.com/developers/api#access-tokens
2. 点击 "Generate new token"
3. 勾选 `file_read` 权限
4. 复制生成的 token（以 `figd_` 开头）

## 返回值格式

### 颜色返回格式

```python
{
    "hex": "#ff4343",
    "rgba": "rgba(255,67,67,1.00)",
    "node": "Rectangle 2",
    "type": "RECTANGLE",
    "path": "Page 1/Frame 1",
    "role": "fill"
}
```

### 效果返回格式

```python
{
    "node": "Button",
    "type": "DROP_SHADOW",
    "path": "Page 1/Frame 1/Button",
    "color": "rgba(0,0,0,0.25)",
    "hex": "#000000",
    "offset_x": 0,
    "offset_y": 4,
    "radius": 8,
    "spread": 0
}
```

### 间距返回格式

```python
{
    "node": "Container",
    "type": "FRAME",
    "path": "Page 1/Container",
    "gap": 16,
    "padding": {"top": 12, "right": 16, "bottom": 12, "left": 16},
    "layoutMode": "VERTICAL",
    "primaryAxisAlign": "SPACE_BETWEEN",
    "counterAxisAlign": "CENTER"
}
```

## 参考文件

所有引用文件均为直接链接，一层深度：

- [README.md](README.md) - 详细文档和使用指南（含 TOC）
- [__init__.py](__init__.py) - Python 模块实现
- [example.py](example.py) - 使用示例代码
- [requirements.txt](requirements.txt) - 依赖列表
- [skill.yaml](skill.yaml) - 技能元数据

## ⚠️ 强制规则（全局生效）

**无论在哪个 ChatID、哪个会话，只要用户要求读取 Figma 文件内容，必须使用 MCP 方式获取！**

- 使用 Figma REST API + `X-Figma-Token` 头
- 从 URL 提取 file ID 和 node ID
- **禁止使用 web_fetch 直接抓取 Figma 网页**（会跳转到登录页）
- 此规则全局生效，跨会话、跨频道均需遵守

## 相关链接

- [Figma API 文档](https://www.figma.com/developers/api)
- [Figma Token 管理](https://www.figma.com/developers/api#access-tokens)

---

🦞 Created by 亏贼马的强壮大龙虾 · MIT License
