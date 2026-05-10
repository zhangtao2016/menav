#!/usr/bin/env python3
"""Convert pintree.json to bookmarks.yml format.

pintree.json: nested {type: "folder", title, children} + {type: "link", title, url, icon}
bookmarks.yml: categories → subcategories → groups → subgroups → sites (max 4 folder levels)
"""

import json
import sys
import os
import re
import yaml

# ---------- config ----------
# https://github.com/Pintree-io/pintree
# chrome-extensions：Pintree Bookmarks Exporter
INPUT = "config/user/pages/pintree.json"
OUTPUT = "config/user/pages/bookmarks.yml"

# mehav max folder depth (categories > subcategories > groups > subgroups)
MAX_DEPTH = 4

# ---------- helpers ----------
def sanitize_filename(name):
    """Sanitize a string for use in filenames."""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    return name


def fa_icon_for(title, url=""):
    """Guess a Font Awesome icon based on title or url keywords."""
    t = title.lower()
    u = url.lower()

    # domain-based
    domain_map = {
        "github.com": "fab fa-github",
        "gitlab.com": "fab fa-gitlab",
        "bitbucket.org": "fab fa-bitbucket",
        "twitter.com": "fab fa-twitter",
        "x.com": "fab fa-x-twitter",
        "facebook.com": "fab fa-facebook",
        "linkedin.com": "fab fa-linkedin",
        "youtube.com": "fab fa-youtube",
        "bilibili.com": "fab fa-bilibili",
        "zhihu.com": "fab fa-zhihu",
        "weibo.com": "fab fa-weibo",
        "stackoverflow.com": "fab fa-stack-overflow",
        "reddit.com": "fab fa-reddit",
        "figma.com": "fab fa-figma",
        "docker.com": "fab fa-docker",
        "npmjs.com": "fab fa-npm",
        "python.org": "fab fa-python",
        "reactjs.org": "fab fa-react",
        "vuejs.org": "fab fa-vuejs",
        "angular.io": "fab fa-angular",
        "nodejs.org": "fab fa-node-js",
        "getbootstrap.com": "fab fa-bootstrap",
        "fontawesome.com": "fab fa-font-awesome",
        "discord.com": "fab fa-discord",
        "telegram.org": "fab fa-telegram",
        "slack.com": "fab fa-slack",
        "notion.so": "fas fa-cube",
        "vercel.com": "fas fa-triangle",
        "netlify.com": "fas fa-cloud-upload-alt",
        "cloudflare.com": "fas fa-cloud",
        "amazon.com": "fab fa-aws",
        "google.com": "fab fa-google",
        "microsoft.com": "fab fa-microsoft",
        "apple.com": "fab fa-apple",
        "aliyun.com": "fas fa-cloud",
        "baidu.com": "fas fa-search",
        "gitee.com": "fas fa-code-branch",
        "leetcode.cn": "fas fa-code",
        "csdn.net": "fas fa-blog",
        "juejin.cn": "fas fa-bookmark",
        "segmentfault.com": "fas fa-question",
    }
    for domain, icon in domain_map.items():
        if domain in u:
            return icon

    # keyword-based
    kw_map = {
        "ai": "fas fa-robot",
        "搜索": "fas fa-search",
        "导航": "fas fa-compass",
        "工具": "fas fa-tools",
        "开发": "fas fa-code",
        "前端": "fas fa-laptop-code",
        "后端": "fas fa-server",
        "设计": "fas fa-paint-brush",
        "安全": "fas fa-shield-alt",
        "数据库": "fas fa-database",
        "学习": "fas fa-graduation-cap",
        "教程": "fas fa-book-open",
        "文档": "fas fa-book",
        "博客": "fas fa-blog",
        "论坛": "fas fa-comments",
        "社区": "fas fa-users",
        "视频": "fas fa-video",
        "音乐": "fas fa-music",
        "图片": "fas fa-image",
        "下载": "fas fa-download",
        "网盘": "fas fa-cloud",
        "邮箱": "fas fa-envelope",
        "翻译": "fas fa-language",
        "笔记": "fas fa-sticky-note",
        "效率": "fas fa-rocket",
        "api": "fas fa-plug",
        "python": "fab fa-python",
        "java": "fab fa-java",
        "javascript": "fab fa-js",
        "golang": "fas fa-code",
        "rust": "fas fa-cog",
        "linux": "fab fa-linux",
        "docker": "fab fa-docker",
        "kubernetes": "fas fa-cubes",
        "git": "fab fa-git-alt",
        "react": "fab fa-react",
        "vue": "fab fa-vuejs",
        "angular": "fab fa-angular",
        "node": "fab fa-node-js",
        "django": "fab fa-python",
        "spring": "fas fa-leaf",
        "mysql": "fas fa-database",
        "redis": "fas fa-server",
        "mongodb": "fas fa-leaf",
        "postgresql": "fas fa-database",
    }
    for kw, icon in kw_map.items():
        if kw in t:
            return icon

    return "fas fa-link"


def build_folder_node(name):
    return {
        "name": name,
        "icon": fa_icon_for(name),
    }


def add_site_node(parent, link):
    title = link.get("title", "")
    url = link.get("url", "")
    site = {
        "name": title,
        "url": url,
        "icon": fa_icon_for(title, url),
    }
    # description from domain only (keep it short)
    domain = re.sub(r'^https?://(www\.)?', '', url).split('/')[0]
    site["description"] = title if len(title) <= 40 else title[:37] + "..."
    parent.setdefault("sites", []).append(site)


# ---------- core conversion ----------
def convert_pintree_to_bookmarks(pintree_data, max_depth=MAX_DEPTH):
    """Convert pintree nested structure to bookmarks categories list."""
    root = pintree_data[0]
    categories = []

    top_children = root.get("children", [])
    top_links = [c for c in top_children if c.get("type") == "link"]
    top_folders = [c for c in top_children if c.get("type") == "folder"]

    # top-level links → single "默认" category
    if top_links:
        default_cat = build_folder_node("默认")
        for link in top_links:
            add_site_node(default_cat, link)
        categories.append(default_cat)

    # top-level folders → categories
    for folder in top_folders:
        cat = build_folder_node(folder.get("title", ""))
        _process_folder(folder, cat, depth=1, max_depth=max_depth)
        categories.append(cat)

    return categories


def _process_folder(folder, parent, depth, max_depth):
    """Recursively process a pintree folder into the mehav hierarchy."""
    children = folder.get("children", [])
    links = [c for c in children if c.get("type") == "link"]
    sub_folders = [c for c in children if c.get("type") == "folder"]

    # Map depth to mehav key name
    depth_key = {
        0: None,  # root, not used
        1: "subcategories",
        2: "groups",
        3: "subgroups",
    }

    # Links at current level → sites (only if no sub_folders to avoid mixed nesting)
    for link in links:
        add_site_node(parent, link)

    # If we've reached max depth, flatten sub_folders' links directly
    if depth >= max_depth:
        for sf in sub_folders:
            _collect_all_links(sf, parent)
        return

    # Process sub_folders into the appropriate sub-level
    key = depth_key.get(depth)
    if key and sub_folders:
        sub_list = []
        for sf in sub_folders:
            sub_node = build_folder_node(sf.get("title", ""))
            _process_folder(sf, sub_node, depth + 1, max_depth)
            sub_list.append(sub_node)
        parent[key] = sub_list


def _collect_all_links(folder, parent):
    """Flatten a folder: add all descendant links to parent's sites."""
    children = folder.get("children", [])
    for child in children:
        if child.get("type") == "link":
            add_site_node(parent, child)
        elif child.get("type") == "folder":
            _collect_all_links(child, parent)


# ---------- output ----------
class _BookmarksDumper(yaml.Dumper):
    """Dumper that avoids unnecessary quoting for bookmark content."""
    pass


def _str_representer(dumper, data):
    # Only quote if string contains YAML-significant characters
    needs_quoting = any(ch in data for ch in [
        ":", "#", "&", "*", "!", ">", "<", "|", "{", "}", "[", "]", "@", "`",
    ]) or data != data.strip() or data in ("true", "false", "yes", "no", "on", "off", "null", "~")
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if needs_quoting:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=None)

_BookmarksDumper.add_representer(str, _str_representer)


def write_bookmarks_yml(categories, output_path):
    header = """\
# 由 pintree-to-bookmarks.py 自动生成
# 源文件: config/user/pages/pintree.json
title: 书签
subtitle: bookmarks
template: bookmarks

categories:
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(
            categories,
            f,
            Dumper=_BookmarksDumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    input_path = os.path.join(repo_root, INPUT.replace("/", os.sep))
    output_path = os.path.join(repo_root, OUTPUT.replace("/", os.sep))

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        pintree = json.load(f)

    print(f"Converting pintree.json → bookmarks.yml (max {MAX_DEPTH} folder levels)...")
    categories = convert_pintree_to_bookmarks(pintree)

    total_sites = count_sites(categories)
    total_cats = len(categories)
    print(f"  {total_cats} categories, {total_sites} sites")

    print(f"Writing {output_path}...")
    write_bookmarks_yml(categories, output_path)
    print("Done.")


def count_sites(categories):
    total = 0
    for cat in categories:
        for site in cat.get("sites", []):
            total += 1
        for sub in cat.get("subcategories", []):
            for site in sub.get("sites", []):
                total += 1
            for grp in sub.get("groups", []):
                for site in grp.get("sites", []):
                    total += 1
                for sgrp in grp.get("subgroups", []):
                    total += len(sgrp.get("sites", []))
    return total


if __name__ == "__main__":
    main()