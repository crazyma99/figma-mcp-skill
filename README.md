# Figma MCP Skill 🎨

通过 Figma REST API 读取设计稿颜色、结构、节点信息的 OpenClaw 技能。

## 目录 (Table of Contents)

- [功能特性](#功能特性)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [安装依赖](#安装依赖)
  - [配置 Token](#配置-token)
- [使用方法](#使用方法)
  - [在 OpenClaw 中使用](#在-openclaw-中使用)
  - [Python 调用](#python-调用)
  - [命令行使用](#命令行使用)
- [API 参考](#api-参考)
  - [get_colors](#get_colors)
  - [get_node_structure](#get_node_structure)
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

- **颜色提取** — 自动提取设计稿中所有 fill、stroke、background 颜色
- **结构读取** — 递归读取节点树，获取元素类型、名称、位置
- **URL 解析** — 自动从 Figma URL 提取 file ID 和 node ID
- **环境检测** — 检查 Python 版本、curl 可用性、网络连通性
- **Token 验证** — 验证 Figma Personal Access Token 有效性
- **跨会话支持** — 无论在哪个 ChatID 都可使用，强制 MCP 方式获取

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

#### 方式一：OpenClaw 技能侧边栏（推荐）

在 OpenClaw WebUI 的技能侧边栏找到 `figma-mcp`，输入你的 Figma PAT。

#### 方式二：环境变量

```bash
export FIGMA_PERSONAL_ACCESS_TOKEN="figd_xxxxxxxxxxxxx"
```

#### 方式三：openclaw.json

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

## 使用方法

### 在 OpenClaw 中使用

直接在聊天中发送 Figma 链接，并说明需要读取什么内容：

```
读取这个 Figma 链接，告诉我里面定义了哪些颜色
https://www.figma.com/design/xxx/Title?node-id=0-1
```

### Python 调用

```python
from skills.figma_mcp import get_colors, get_node_structure, parse_figma_url

# 读取颜色
colors = get_colors("https://www.figma.com/design/xxx/Title?node-id=0-1")
for c in colors:
    print(f"{c['hex']} - {c['node']}")

# 读取结构
structure = get_node_structure("https://www.figma.com/design/xxx/Title?node-id=6-2")
print(f"{structure['name']}: {len(structure['children'])} 个子元素")

# 解析 URL
info = parse_figma_url("https://www.figma.com/design/xxx/Title?node-id=0-1")
print(f"file_id: {info['file_id']}, node_id: {info['node_id']}")
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

| 参数 | 类型 | 说明 |
|------|------|------|
| url | str | Figma URL |
| token | str | PAT（None 时读取环境变量） |

**返回：** 颜色列表，每项包含 hex、rgba、node、type、path、role

### get_node_structure

获取 Figma 节点结构。

```python
get_node_structure(url: str, token: Optional[str] = None) -> Dict
```

**返回：** 节点字典，包含 name、type、id、children

### parse_figma_url

从 URL 提取 file ID 和 node ID。

```python
parse_figma_url(url: str) -> Dict[str, str]
```

**返回：** 包含 file_id、node_id、title 的字典

### check_environment

检查运行环境。

```python
check_environment() -> Dict
```

**返回：** Python 版本、curl 状态、网络连通性、Token 环境变量状态

### check_token

验证 Figma Token 有效性。

```python
check_token(token: Optional[str] = None) -> Dict
```

**返回：** valid、user、email、id

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
├── skill.yaml        # 技能元数据
├── README.md         # 详细文档（含 TOC）
├── __init__.py       # Python 模块实现
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

## 许可

MIT License — Created by 亏贼马的强壮大龙虾 🦞
