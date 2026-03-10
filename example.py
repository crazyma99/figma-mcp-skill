#!/usr/bin/env python3
"""
Figma MCP Skill - 使用示例

演示如何使用 figma-mcp skill 读取 Figma 设计稿。
"""

import sys
import json
from skills.figma_mcp import (
    get_colors,
    get_node_structure,
    parse_figma_url,
    check_environment,
    check_token
)


def main():
    # ============================================================
    # 1. 环境检测
    # ============================================================
    print("=== 环境检测 ===")
    env = check_environment()
    print(f"Python: {env['python']['version']} (OK: {env['python']['ok']})")
    print(f"curl: {env['curl']['available']} ({env['curl'].get('version', 'N/A')})")
    print(f"网络: {env['network']['connected']}")
    print(f"Token 环境变量: {env['token_env']}")
    print()
    
    # ============================================================
    # 2. Token 验证
    # ============================================================
    print("=== Token 验证 ===")
    token_check = check_token()
    if token_check["valid"]:
        print(f"✓ Token 有效")
        print(f"  用户: {token_check['user']}")
        print(f"  邮箱: {token_check.get('email', 'N/A')}")
    else:
        print(f"✗ Token 无效: {token_check['error']}")
        return 1
    print()
    
    # ============================================================
    # 3. URL 解析示例
    # ============================================================
    print("=== URL 解析 ===")
    test_urls = [
        "https://www.figma.com/design/H895GidT9BjHSQ2mBfIjxl/Untitled?node-id=0-1",
        "https://www.figma.com/file/abc123/MyDesign?node-id=6-2",
    ]
    for url in test_urls:
        info = parse_figma_url(url)
        print(f"URL: {url}")
        print(f"  file_id: {info['file_id']}")
        print(f"  node_id: {info['node_id']}")
        print(f"  title: {info['title']}")
    print()
    
    # ============================================================
    # 4. 读取颜色
    # ============================================================
    print("=== 读取颜色 ===")
    url = "https://www.figma.com/design/H895GidT9BjHSQ2mBfIjxl/Untitled?node-id=0-1"
    print(f"URL: {url}")
    
    try:
        colors = get_colors(url)
        print(f"找到 {len(colors)} 个颜色:")
        for c in colors:
            print(f"  {c['hex']} / {c['rgba']} - {c['node']} ({c['role']})")
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # ============================================================
    # 5. 读取节点结构
    # ============================================================
    print("=== 读取节点结构 ===")
    try:
        structure = get_node_structure(url)
        print(f"节点: {structure['name']} ({structure['type']})")
        print(f"ID: {structure['id']}")
        print(f"子元素数量: {len(structure['children'])}")
        for child in structure['children'][:5]:  # 只显示前5个
            print(f"  - {child['name']} ({child['type']})")
        if len(structure['children']) > 5:
            print(f"  ... 还有 {len(structure['children']) - 5} 个元素")
    except Exception as e:
        print(f"错误: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
