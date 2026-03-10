#!/usr/bin/env python3
"""
Figma MCP Skill 使用示例

展示如何使用颜色提取、结构读取、图片导出、效果识别、透明度、间距等功能。
"""

import os
import sys

# 添加技能路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import (
    get_colors,
    get_node_structure,
    parse_figma_url,
    export_image,
    export_image_from_url,
    get_effects,
    get_opacity,
    get_spacing,
    check_environment,
    check_token,
)

# 示例 URL
EXAMPLE_URL = "https://www.figma.com/design/nk0zS9NeSNifrO548qp7Nj/Untitled?node-id=0-1"


def main():
    print("=" * 60)
    print("Figma MCP Skill 示例")
    print("=" * 60)
    
    # 1. 环境检测
    print("\n🔍 环境检测:")
    env = check_environment()
    print(f"  Python: {env['python']['version']}")
    print(f"  curl: {'可用' if env['curl']['available'] else '不可用'}")
    print(f"  网络: {'已连接' if env['network']['connected'] else '未连接'}")
    
    # 2. Token 验证
    print("\n🔑 Token 验证:")
    try:
        token_info = check_token()
        print(f"  有效: {token_info['valid']}")
        print(f"  用户: {token_info.get('user', 'N/A')}")
    except Exception as e:
        print(f"  错误: {e}")
        return
    
    # 3. URL 解析
    print("\n🔗 URL 解析:")
    info = parse_figma_url(EXAMPLE_URL)
    print(f"  File ID: {info['file_id']}")
    print(f"  Node ID: {info['node_id']}")
    print(f"  Title: {info['title']}")
    
    # 4. 读取颜色
    print("\n🎨 颜色提取:")
    try:
        colors = get_colors(EXAMPLE_URL)
        print(f"  找到 {len(colors)} 个颜色")
        # 显示前5个
        for c in colors[:5]:
            print(f"  {c['hex']} ({c['role']}) - {c['node']}")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 5. 读取结构
    print("\n📐 节点结构:")
    try:
        structure = get_node_structure(EXAMPLE_URL)
        print(f"  名称: {structure['name']}")
        print(f"  类型: {structure['type']}")
        print(f"  子元素: {len(structure['children'])}")
        if 'width' in structure:
            print(f"  尺寸: {structure['width']}x{structure['height']}")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 6. 读取效果
    print("\n✨ 效果提取 (阴影/模糊):")
    try:
        effects = get_effects(EXAMPLE_URL)
        print(f"  找到 {len(effects)} 个效果")
        for e in effects[:5]:
            print(f"  {e['node']}: {e['type']} - {e.get('color', 'N/A')}")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 7. 读取透明度
    print("\n🌓 透明度识别:")
    try:
        opacities = get_opacity(EXAMPLE_URL)
        print(f"  找到 {len(opacities)} 个非完全不透明节点")
        for o in opacities[:5]:
            print(f"  {o['node']}: {o['percent']}")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 8. 读取间距
    print("\n📏 间距识别 (gap/padding):")
    try:
        spacings = get_spacing(EXAMPLE_URL)
        print(f"  找到 {len(spacings)} 个有间距信息的节点")
        for s in spacings[:5]:
            parts = []
            if 'gap' in s:
                parts.append(f"gap={s['gap']}")
            if 'padding' in s:
                p = s['padding']
                parts.append(f"pad={p['top']}/{p['right']}/{p['bottom']}/{p['left']}")
            if 'layoutMode' in s:
                parts.append(f"layout={s['layoutMode']}")
            print(f"  {s['node']}: {' | '.join(parts)}")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 9. 图片导出
    print("\n🖼️ 图片导出:")
    try:
        images = export_image_from_url(EXAMPLE_URL, format="png", scale=2)
        for node_id, url in images.items():
            print(f"  {node_id}: {url[:60]}...")
    except Exception as e:
        print(f"  错误: {e}")
    
    print("\n" + "=" * 60)
    print("示例完成！")


if __name__ == "__main__":
    main()
