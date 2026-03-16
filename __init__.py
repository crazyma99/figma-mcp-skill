"""
Figma MCP Skill - Figma 设计稿读取工具

通过 Figma REST API 读取设计稿颜色、结构、节点信息、效果、间距、透明度、导出图片。
支持 URL 自动解析和环境检测。

Usage:
    from skills.figma_mcp import (
        get_colors, get_node_structure, parse_figma_url,
        export_image, get_effects, get_opacity, get_spacing
    )
    
    colors = get_colors("https://www.figma.com/design/xxx/Title?node-id=0-1")
    structure = get_node_structure("https://www.figma.com/design/xxx/Title?node-id=6-2")
    img_url = export_image("fileId", "nodeId", format="png", scale=2)
"""

__version__ = "1.1.0"
__author__ = "亏贼马"

import os
import re
import sys
import json
import subprocess
from typing import Optional, Dict, List, Any, Tuple

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
            pat = config.get("skills", {}).get("entries", {}).get("figma-mcp", {}).get("apiKey")
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


def _rgba_from_figma_color(c: Dict) -> Tuple[int, int, int, float]:
    """将 Figma 颜色对象转换为 RGBA 值"""
    r = int(c.get("r", 0) * 255)
    g = int(c.get("g", 0) * 255)
    b = int(c.get("b", 0) * 255)
    a = c.get("a", 1)
    return r, g, b, a


# ============================================================================
# 颜色提取 (Color Extraction)
# ============================================================================

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
            r, g, b, a = _rgba_from_figma_color(c)
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
            r, g, b, a = _rgba_from_figma_color(c)
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
        r, g, b, a = _rgba_from_figma_color(bg)
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


# ============================================================================
# 效果提取 (Effect Extraction) - 阴影、模糊等
# ============================================================================

def _extract_effects_from_node(node: Dict, path: str = "") -> List[Dict[str, Any]]:
    """递归提取节点中的效果（阴影、模糊等）"""
    effects = []
    node_name = node.get("name", "unnamed")
    node_type = node.get("type", "UNKNOWN")
    current_path = f"{path}/{node_name}" if path else node_name
    
    for effect in node.get("effects", []):
        if not effect.get("visible", True):
            continue
        
        effect_type = effect.get("type", "")
        effect_entry = {
            "node": node_name,
            "type": effect_type,
            "path": current_path,
        }
        
        if effect_type == "DROP_SHADOW":
            c = effect.get("color", {})
            r, g, b, a = _rgba_from_figma_color(c)
            offset = effect.get("offset", {})
            effect_entry.update({
                "color": f"rgba({r},{g},{b},{a:.2f})",
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "offset_x": offset.get("x", 0),
                "offset_y": offset.get("y", 0),
                "radius": effect.get("radius", 0),
                "spread": effect.get("spread", 0),
            })
        
        elif effect_type == "INNER_SHADOW":
            c = effect.get("color", {})
            r, g, b, a = _rgba_from_figma_color(c)
            offset = effect.get("offset", {})
            effect_entry.update({
                "color": f"rgba({r},{g},{b},{a:.2f})",
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "offset_x": offset.get("x", 0),
                "offset_y": offset.get("y", 0),
                "radius": effect.get("radius", 0),
                "spread": effect.get("spread", 0),
            })
        
        elif effect_type == "LAYER_BLUR":
            effect_entry.update({
                "radius": effect.get("radius", 0),
            })
        
        elif effect_type == "BACKGROUND_BLUR":
            effect_entry.update({
                "radius": effect.get("radius", 0),
            })
        
        effects.append(effect_entry)
    
    # 递归子节点
    for child in node.get("children", []):
        effects.extend(_extract_effects_from_node(child, current_path))
    
    return effects


# ============================================================================
# 透明度提取 (Opacity Extraction)
# ============================================================================

def _extract_opacity_from_node(node: Dict, path: str = "") -> List[Dict[str, Any]]:
    """递归提取节点透明度"""
    results = []
    node_name = node.get("name", "unnamed")
    node_type = node.get("type", "UNKNOWN")
    current_path = f"{path}/{node_name}" if path else node_name
    opacity = node.get("opacity", 1.0)
    
    # 只记录非完全不透明的节点
    if opacity < 1.0:
        results.append({
            "node": node_name,
            "type": node_type,
            "path": current_path,
            "opacity": opacity,
            "percent": f"{int(opacity * 100)}%"
        })
    
    # 递归子节点
    for child in node.get("children", []):
        results.extend(_extract_opacity_from_node(child, current_path))
    
    return results


# ============================================================================
# 间距提取 (Spacing Extraction) - gap, margin, padding
# ============================================================================

def _extract_spacing_from_node(node: Dict, path: str = "") -> List[Dict[str, Any]]:
    """递归提取节点间距信息（gap, padding, itemSpacing）"""
    results = []
    node_name = node.get("name", "unnamed")
    node_type = node.get("type", "UNKNOWN")
    current_path = f"{path}/{node_name}" if path else node_name
    
    spacing_info = {}
    
    # itemSpacing (auto-layout gap)
    item_spacing = node.get("itemSpacing")
    if item_spacing is not None:
        spacing_info["gap"] = item_spacing
    
    # padding (auto-layout padding)
    padding_top = node.get("paddingTop")
    padding_right = node.get("paddingRight")
    padding_bottom = node.get("paddingBottom")
    padding_left = node.get("paddingLeft")
    
    if any(p is not None for p in [padding_top, padding_right, padding_bottom, padding_left]):
        spacing_info["padding"] = {
            "top": padding_top or 0,
            "right": padding_right or 0,
            "bottom": padding_bottom or 0,
            "left": padding_left or 0,
        }
    
    # counterAxisSpacing (auto-layout secondary axis gap)
    counter_spacing = node.get("counterAxisSpacing")
    if counter_spacing is not None:
        spacing_info["counterAxisSpacing"] = counter_spacing
    
    # 主轴对齐和副轴对齐
    layout_mode = node.get("layoutMode")
    if layout_mode:
        spacing_info["layoutMode"] = layout_mode
        spacing_info["primaryAxisAlign"] = node.get("primaryAxisAlignItems", "MIN")
        spacing_info["counterAxisAlign"] = node.get("counterAxisAlignItems", "MIN")
    
    # constraints (margin-like behavior)
    constraints = node.get("constraints", {})
    if constraints:
        spacing_info["constraints"] = {
            "horizontal": constraints.get("horizontal", ""),
            "vertical": constraints.get("vertical", ""),
        }
    
    if spacing_info:
        results.append({
            "node": node_name,
            "type": node_type,
            "path": current_path,
            **spacing_info
        })
    
    # 递归子节点
    for child in node.get("children", []):
        results.extend(_extract_spacing_from_node(child, current_path))
    
    return results


# ============================================================================
# 结构提取 (Structure Extraction)
# ============================================================================

def _extract_structure(node: Dict, path: str = "") -> Dict[str, Any]:
    """递归提取节点结构"""
    current_path = f"{path}/{node.get('name','')}" if path else node.get("name", "")
    structure = {
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "path": current_path,
        "opacity": node.get("opacity", 1.0),
        "children": []
    }
    
    # 添加布局信息
    bbox = node.get("absoluteBoundingBox", {})
    if bbox:
        structure["x"] = bbox.get("x", 0)
        structure["y"] = bbox.get("y", 0)
        structure["width"] = bbox.get("width", 0)
        structure["height"] = bbox.get("height", 0)
    
    # 圆角
    corner_radius = node.get("cornerRadius")
    if corner_radius:
        structure["cornerRadius"] = corner_radius
    
    for child in node.get("children", []):
        structure["children"].append(_extract_structure(child, current_path))
    
    return structure


# ============================================================================
# 图片导出 (Image Export)
# ============================================================================

def export_image(
    file_id: str,
    node_ids: str,
    token: Optional[str] = None,
    format: str = "png",
    scale: int = 1
) -> Dict[str, str]:
    """
    导出 Figma 节点为图片
    
    Args:
        file_id: Figma 文件 ID
        node_ids: 节点 ID，多个用逗号分隔（如 "0:1,13:2"）
        token: Figma PAT
        format: 图片格式 ("png", "jpg", "svg", "pdf")
        scale: 缩放比例 (1, 2, 3, 4)
    
    Returns:
        字典，key 为 node ID，value 为图片 URL
    """
    tok = get_token(token)
    
    endpoint = f"images/{file_id}?ids={node_ids}&format={format}&scale={scale}"
    data = _api_request(endpoint, tok)
    
    err = data.get("err")
    if err:
        raise RuntimeError(f"Figma 图片导出错误: {err}")
    
    return data.get("images", {})


def export_image_from_url(
    url: str,
    token: Optional[str] = None,
    format: str = "png",
    scale: int = 2
) -> Dict[str, str]:
    """
    从 Figma URL 导出节点为图片
    
    Args:
        url: Figma 设计稿 URL
        token: Figma PAT
        format: 图片格式
        scale: 缩放比例
    
    Returns:
        字典，key 为 node ID，value 为图片 URL
    """
    info = parse_figma_url(url)
    node_id = info["node_id"] or "0:1"  # 默认导出根节点
    return export_image(info["file_id"], node_id, token, format, scale)


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
        节点结构字典，包含 name、type、id、children、位置信息
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


def get_effects(url: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    提取节点效果（阴影、模糊等）
    
    Args:
        url: Figma 设计稿 URL
        token: Figma PAT
    
    Returns:
        效果列表，每项包含 type、color、offset、radius 等
    """
    tok = get_token(token)
    info = parse_figma_url(url)
    
    if info["node_id"]:
        endpoint = f"files/{info['file_id']}/nodes?ids={info['node_id']}"
    else:
        endpoint = f"files/{info['file_id']}"
    
    data = _api_request(endpoint, tok)
    
    effects = []
    nodes = data.get("nodes", {})
    if nodes:
        for node_data in nodes.values():
            doc = node_data.get("document", {})
            effects.extend(_extract_effects_from_node(doc))
    else:
        doc = data.get("document", {})
        effects.extend(_extract_effects_from_node(doc))
    
    return effects


def get_opacity(url: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    提取非完全不透明节点的透明度信息
    
    Args:
        url: Figma 设计稿 URL
        token: Figma PAT
    
    Returns:
        透明度列表，每项包含 node、type、opacity、percent
    """
    tok = get_token(token)
    info = parse_figma_url(url)
    
    if info["node_id"]:
        endpoint = f"files/{info['file_id']}/nodes?ids={info['node_id']}"
    else:
        endpoint = f"files/{info['file_id']}"
    
    data = _api_request(endpoint, tok)
    
    results = []
    nodes = data.get("nodes", {})
    if nodes:
        for node_data in nodes.values():
            doc = node_data.get("document", {})
            results.extend(_extract_opacity_from_node(doc))
    else:
        doc = data.get("document", {})
        results.extend(_extract_opacity_from_node(doc))
    
    return results


def get_spacing(url: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    提取间距信息（gap、padding、auto-layout 间距）
    
    Args:
        url: Figma 设计稿 URL
        token: Figma PAT
    
    Returns:
        间距列表，每项包含 gap、padding、layoutMode 等
    """
    tok = get_token(token)
    info = parse_figma_url(url)
    
    if info["node_id"]:
        endpoint = f"files/{info['file_id']}/nodes?ids={info['node_id']}"
    else:
        endpoint = f"files/{info['file_id']}"
    
    data = _api_request(endpoint, tok)
    
    results = []
    nodes = data.get("nodes", {})
    if nodes:
        for node_data in nodes.values():
            doc = node_data.get("document", {})
            results.extend(_extract_spacing_from_node(doc))
    else:
        doc = data.get("document", {})
        results.extend(_extract_spacing_from_node(doc))
    
    return results


# ============================================================================
# 批量导出 (Batch Export)
# ============================================================================

def collect_icons(
    structure: Dict[str, Any],
    min_width: int = 32,
    max_width: int = 128,
    min_height: int = 32,
    max_height: int = 128,
    name_contains: Optional[str] = "icon"
) -> List[Dict[str, Any]]:
    """
    从节点结构中收集图标节点
    
    Args:
        structure: 节点结构（来自 get_node_structure）
        min_width: 最小宽度筛选
        max_width: 最大宽度筛选
        min_height: 最小高度筛选
        max_height: 最大高度筛选
        name_contains: 名称关键词筛选，None 不筛选
    
    Returns:
        图标节点列表，包含 id node_id name width height path
    """
    def _collect(node: Dict[str, Any], path: str = '') -> List[Dict[str, Any]]:
        icons = []
        node_name = node.get('name', '').lower()
        node_width = node.get('width', 0)
        node_height = node.get('height', 0)
        current_path = path + '/' + node.get('name', '')
        
        # 筛选条件
        size_ok = (min_width <= node_width <= max_width) and (min_height <= node_height <= max_height)
        name_ok = (name_contains is None) or (name_contains.lower() in node_name)
        
        if size_ok and name_ok:
            node_id = node['id']
            icons.append({
                'id': node_id.replace(':', '-'),
                'node_id': node_id,
                'name': node.get('name', f'icon-{node_id}'),
                'path': current_path,
                'width': node_width,
                'height': node_height,
            })
        
        # 递归遍历子节点
        for child in node.get('children', []):
            icons.extend(_collect(child, current_path))
        
        return icons
    
    return _collect(structure)


def batch_export_icons(
    file_id: str,
    icons: List[Dict[str, Any]],
    output_dir: str,
    token: Optional[str] = None,
    format: str = "png",
    scale: int = 2
) -> Dict[str, Any]:
    """
    批量导出图标到本地目录
    
    Args:
        file_id: Figma 文件 ID
        icons: 图标列表（来自 collect_icons）
        output_dir: 输出目录
        token: Figma PAT
        format: 图片格式 png/jpg/svg/pdf
        scale: 缩放比例
    
    Returns:
        导出结果统计
    """
    import urllib.request
    os.makedirs(output_dir, exist_ok=True)
    
    tok = get_token(token)
    exported = []
    failed = []
    
    for icon in icons:
        node_id = icon['node_id']
        icon_id = icon['id']
        filename = os.path.join(output_dir, f"{icon_id}.{format}")
        
        try:
            result = export_image(file_id, node_id, tok, format=format, scale=scale)
            if result:
                for nid, url in result.items():
                    if url:
                        urllib.request.urlretrieve(url, filename)
                        if os.path.exists(filename):
                            size = os.path.getsize(filename)
                            exported.append({
                                **icon,
                                'path': filename,
                                'size': size,
                                'url': url
                            })
                        else:
                            failed.append({**icon, 'error': 'File not saved'})
                    else:
                        failed.append({**icon, 'error': 'Empty URL'})
            else:
                failed.append({**icon, 'error': 'No result'})
        except Exception as e:
            failed.append({**icon, 'error': str(e)})
    
    return {
        'total': len(icons),
        'exported': len(exported),
        'failed': len(failed),
        'exported_list': exported,
        'failed_list': failed
    }


def collect_and_export_icons(
    url: str,
    output_dir: str,
    token: Optional[str] = None,
    format: str = "png",
    scale: int = 2,
    min_width: int = 32,
    max_width: int = 128,
    min_height: int = 32,
    max_height: int = 128,
    name_contains: Optional[str] = "icon"
) -> Dict[str, Any]:
    """
    一键收集并批量导出图标
    
    Args:
        url: Figma 设计稿 URL
        output_dir: 输出目录
        token: Figma PAT
        format: 图片格式
        scale: 缩放比例
        min/max width/height: 尺寸筛选
        name_contains: 名称关键词筛选
    
    Returns:
        导出结果统计
    """
    structure = get_node_structure(url, token)
    icons = collect_icons(structure, min_width, max_width, min_height, max_height, name_contains)
    info = parse_figma_url(url)
    file_id = info['file_id']
    return batch_export_icons(file_id, icons, output_dir, token, format, scale)


# ============================================================================
# 模块导出
# ============================================================================

__all__ = [
    # 基础功能
    "get_colors",
    "get_node_structure",
    "parse_figma_url",
    "check_environment",
    "check_token",
    "get_token",
    "check_python_version",
    "check_curl_available",
    "check_network_connectivity",
    # 图片导出
    "export_image",
    "export_image_from_url",
    # 批量导出
    "collect_icons",
    "batch_export_icons",
    "collect_and_export_icons",
    # 效果/透明度/间距
    "get_effects",
    "get_opacity",
    "get_spacing",
]
