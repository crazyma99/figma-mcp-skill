"""
Figma MCP Skill - Figma 设计稿读取工具

通过 Figma REST API 读取设计稿颜色、结构、节点信息。
支持 URL 自动解析和环境检测。

Usage:
    from skills.figma_mcp import get_colors, get_node_structure, parse_figma_url
    
    colors = get_colors("https://www.figma.com/design/xxx/Title?node-id=0-1")
    structure = get_node_structure("https://www.figma.com/design/xxx/Title?node-id=6-2")
"""

__version__ = "1.0.0"
__author__ = "亏贼马"

import os
import re
import sys
import json
import subprocess
from typing import Optional, Dict, List, Any

# ============================================================================
# 环境检测 (Environment Detection)
# ============================================================================

def check_python_version(min_version=(3, 10)):
    """检查 Python 版本是否符合要求"""
    current = sys.version_info[:2]
    if current < min_version:
        raise RuntimeError(
            f"Python {'.'.join(map(str, min_version))}+ required, "
            f"got {'.'.join(map(str, current))}"
        )
    return {"version": f"{current[0]}.{current[1]}", "ok": True}


def check_curl_available():
    """检查 curl 是否可用"""
    try:
        result = subprocess.run(
            ["curl", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return {"available": True, "version": version_line}
        return {"available": False, "error": "curl returned non-zero"}
    except FileNotFoundError:
        return {"available": False, "error": "curl not found"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def check_network_connectivity():
    """检查网络连通性"""
    try:
        import socket
        socket.create_connection(("api.figma.com", 443), timeout=5)
        return {"connected": True, "host": "api.figma.com"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def check_environment():
    """完整环境检测"""
    return {
        "python": check_python_version(),
        "curl": check_curl_available(),
        "network": check_network_connectivity(),
        "token_env": bool(os.environ.get("FIGMA_PERSONAL_ACCESS_TOKEN"))
    }


# ============================================================================
# Token 管理 (Token Management)
# ============================================================================

def get_token(token: Optional[str] = None) -> str:
    """获取 Figma Token，优先使用传入参数，其次环境变量"""
    if token:
        return token
    
    env_token = os.environ.get("FIGMA_PERSONAL_ACCESS_TOKEN")
    if env_token:
        return env_token
    
    # 尝试从 openclaw.json 读取
    try:
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            pat = config.get("skills", {}).get("entries", {}).get("figma-mcp", {}).get("pat")
            if pat:
                return pat
    except Exception:
        pass
    
    raise ValueError(
        "未找到 Figma Token。请设置 FIGMA_PERSONAL_ACCESS_TOKEN 环境变量 "
        "或在 OpenClaw 技能侧边栏配置 PAT。"
    )


def check_token(token: Optional[str] = None) -> Dict[str, Any]:
    """验证 Token 有效性"""
    try:
        tok = get_token(token)
        import requests
        resp = requests.get(
            "https://api.figma.com/v1/me",
            headers={"X-Figma-Token": tok},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "user": data.get("handle", "unknown"),
                "email": data.get("email", ""),
                "id": data.get("id", "")
            }
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


# ============================================================================
# URL 解析 (URL Parsing)
# ============================================================================

def parse_figma_url(url: str) -> Dict[str, str]:
    """
    从 Figma URL 提取 file ID 和 node ID
    
    支持格式:
    - https://www.figma.com/design/{file_id}/{title}?node-id={node_id}
    - https://www.figma.com/file/{file_id}/{title}?node-id={node_id}
    """
    # 提取 file ID
    file_match = re.search(r'/design/([a-zA-Z0-9]+)', url)
    if not file_match:
        file_match = re.search(r'/file/([a-zA-Z0-9]+)', url)
    
    if not file_match:
        raise ValueError(f"无法从 URL 提取 file ID: {url}")
    
    file_id = file_match.group(1)
    
    # 提取 node ID
    node_match = re.search(r'[?&]node-id=([^&]+)', url)
    node_id = node_match.group(1) if node_match else None
    
    # 提取标题
    title_match = re.search(r'/design/[a-zA-Z0-9]+/([^?]+)', url)
    if not title_match:
        title_match = re.search(r'/file/[a-zA-Z0-9]+/([^?]+)', url)
    title = title_match.group(1) if title_match else "Untitled"
    
    return {
        "file_id": file_id,
        "node_id": node_id,
        "title": title
    }


# ============================================================================
# API 调用 (API Calls)
# ============================================================================

def _api_request(endpoint: str, token: str) -> Dict[str, Any]:
    """通用 API 请求"""
    import requests
    url = f"https://api.figma.com/v1/{endpoint}"
    resp = requests.get(
        url,
        headers={"X-Figma-Token": token},
        timeout=15
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Figma API 错误: HTTP {resp.status_code} - {resp.text[:200]}")
    return resp.json()


def _extract_colors_from_node(node: Dict, path: str = "") -> List[Dict[str, Any]]:
    """递归提取节点中的颜色"""
    colors = []
    node_name = node.get("name", "unnamed")
    node_type = node.get("type", "UNKNOWN")
    current_path = f"{path}/{node_name}" if path else node_name
    
    # 提取 fills
    for fill in node.get("fills", []):
        if fill.get("type") == "SOLID" and fill.get("visible", True):
            c = fill.get("color", {})
            r = int(c.get("r", 0) * 255)
            g = int(c.get("g", 0) * 255)
            b = int(c.get("b", 0) * 255)
            a = c.get("a", 1)
            colors.append({
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "rgba": f"rgba({r},{g},{b},{a:.2f})",
                "node": node_name,
                "type": node_type,
                "path": current_path,
                "role": "fill"
            })
    
    # 提取 strokes
    for stroke in node.get("strokes", []):
        if stroke.get("type") == "SOLID" and stroke.get("visible", True):
            c = stroke.get("color", {})
            r = int(c.get("r", 0) * 255)
            g = int(c.get("g", 0) * 255)
            b = int(c.get("b", 0) * 255)
            a = c.get("a", 1)
            colors.append({
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "rgba": f"rgba({r},{g},{b},{a:.2f})",
                "node": node_name,
                "type": node_type,
                "path": current_path,
                "role": "stroke"
            })
    
    # 提取背景色
    bg = node.get("backgroundColor")
    if bg:
        r = int(bg.get("r", 0) * 255)
        g = int(bg.get("g", 0) * 255)
        b = int(bg.get("b", 0) * 255)
        a = bg.get("a", 1)
        colors.append({
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgba": f"rgba({r},{g},{b},{a:.2f})",
            "node": node_name,
            "type": node_type,
            "path": current_path,
            "role": "background"
        })
    
    # 递归子节点
    for child in node.get("children", []):
        colors.extend(_extract_colors_from_node(child, current_path))
    
    return colors


def _extract_structure(node: Dict, path: str = "") -> Dict[str, Any]:
    """递归提取节点结构"""
    current_path = f"{path}/{node.get('name','')}" if path else node.get("name", "")
    structure = {
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "path": current_path,
        "children": []
    }
    
    for child in node.get("children", []):
        structure["children"].append(_extract_structure(child, current_path))
    
    return structure


# ============================================================================
# 公开 API (Public API)
# ============================================================================

def get_colors(url: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    从 Figma 设计稿提取所有颜色
    
    Args:
        url: Figma 设计稿 URL
        token: Figma PAT（None 时从环境变量读取）
    
    Returns:
        颜色列表，每项包含 hex、rgba、node、type、path、role
    """
    tok = get_token(token)
    info = parse_figma_url(url)
    
    if info["node_id"]:
        endpoint = f"files/{info['file_id']}/nodes?ids={info['node_id']}"
    else:
        endpoint = f"files/{info['file_id']}"
    
    data = _api_request(endpoint, tok)
    
    colors = []
    nodes = data.get("nodes", {})
    if nodes:
        for node_data in nodes.values():
            doc = node_data.get("document", {})
            colors.extend(_extract_colors_from_node(doc))
    else:
        doc = data.get("document", {})
        colors.extend(_extract_colors_from_node(doc))
    
    # 去重（按 hex + node）
    seen = set()
    unique = []
    for c in colors:
        key = (c["hex"], c["node"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    
    return unique


def get_node_structure(url: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    获取 Figma 节点结构
    
    Args:
        url: Figma 设计稿 URL
        token: Figma PAT（None 时从环境变量读取）
    
    Returns:
        节点结构字典，包含 name、type、id、children
    """
    tok = get_token(token)
    info = parse_figma_url(url)
    
    if info["node_id"]:
        endpoint = f"files/{info['file_id']}/nodes?ids={info['node_id']}"
    else:
        endpoint = f"files/{info['file_id']}"
    
    data = _api_request(endpoint, tok)
    
    nodes = data.get("nodes", {})
    if nodes:
        node_data = list(nodes.values())[0]
        doc = node_data.get("document", {})
    else:
        doc = data.get("document", {})
    
    return _extract_structure(doc)


# ============================================================================
# 模块导出
# ============================================================================

__all__ = [
    "get_colors",
    "get_node_structure",
    "parse_figma_url",
    "check_environment",
    "check_token",
    "get_token",
    "check_python_version",
    "check_curl_available",
    "check_network_connectivity",
]
