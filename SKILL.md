---
name: figma-mcp
description: Figma MCP 读取技能 - 通过 Figma REST API 读取设计稿颜色、结构、节点信息，支持 URL 自动解析
metadata:
  openclaw:
    emoji: "🎨"
    requires:
      config: ["skills.entries.figma-mcp.pat"]
    primaryEnv: "FIGMA_PERSONAL_ACCESS_TOKEN"
---

# Figma MCP 读取技能 (Figma MCP Reader)

✅ **已验证可用** (2026-03-10) - 支持读取颜色、结构、节点详情，URL 自动解析

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

在 OpenClaw WebUI 的技能侧边栏配置：

| 字段 | 说明 |
|------|------|
| **PAT** | Figma Personal Access Token |

或设置环境变量：

```bash
export FIGMA_PERSONAL_ACCESS_TOKEN="figd_xxxxxxxxxxxxx"
```

### 读取颜色

```python
from skills.figma_mcp import get_colors, parse_figma_url

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

### 解析 URL

```python
from skills.figma_mcp import parse_figma_url

info = parse_figma_url("https://www.figma.com/design/abc123/Title?node-id=6-2")
print(info)  # {'file_id': 'abc123', 'node_id': '6-2'}
```

## 核心功能

### 1. 颜色提取
- 自动提取所有 fill、stroke、background 颜色
- 输出 HEX 和 RGBA 格式
- 去重并记录出现位置

### 2. 结构读取
- 递归遍历节点树
- 获取元素类型、名称、位置
- 支持按 node-id 定位

### 3. URL 自动解析
- 从 Figma URL 自动提取 file ID
- 自动提取 node-id 参数
- 支持多种 URL 格式

### 4. 环境检测
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

**返回：** `list[dict]` — 颜色列表，每项包含 hex、rgba、node、type

### get_node_structure(url, token=None)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | 必填 | Figma 设计稿 URL |
| token | str | None | PAT（None 时读取环境变量） |

**返回：** `dict` — 节点结构，包含 name、type、children

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
        "pat": "figd_xxxxxxxxxxxxx"
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
[
    {
        "hex": "#ff4343",
        "rgba": "rgba(255,67,67,1.00)",
        "node": "Rectangle 2",
        "type": "RECTANGLE",
        "path": "Page 1/Frame 1"
    }
]
```

### 结构返回格式

```python
{
    "name": "Frame 1",
    "type": "FRAME",
    "id": "6:2",
    "children": [
        {"name": "Rectangle 1", "type": "RECTANGLE", "id": "6:3"}
    ]
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
