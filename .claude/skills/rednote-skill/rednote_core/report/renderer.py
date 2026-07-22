"""HTML report renderer using Jinja2."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_templates_dir() -> str:
    """Get the path to the templates directory."""
    return str(Path(__file__).parent / "templates")


def render_report(
    template_name: str,
    data: dict[str, Any],
    output_path: str | None = None,
) -> str:
    """Render an HTML report from a template."""
    env = Environment(
        loader=FileSystemLoader(get_templates_dir()),
        autoescape=select_autoescape(["html"]),
    )

    template = env.get_template(template_name)

    data.setdefault("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    html = template.render(**data)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    return html


def render_search_report(
    keyword: str,
    items: list,
    output_dir: str = "data/reports",
) -> str:
    """Render a search results report."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-search-{keyword}.html"
    output_path = os.path.join(output_dir, filename)

    item_dicts = []
    for item in items:
        item_dicts.append({
            "note_id": item.note_id,
            "title": item.title,
            "desc": item.desc,
            "type": item.type,
            "xsec_token": item.xsec_token,
            "user": item.user,
            "interact_info": item.interact_info,
            "tag_list": item.tag_list,
            "image_list": item.image_list,
            "time": item.time,
            "ip_location": item.ip_location,
        })

    render_report("search.html", {"keyword": keyword, "items": item_dicts}, output_path)
    return output_path


def render_daily_report(
    user_id: str,
    notes: list,
    output_dir: str = "data/reports",
) -> str:
    """Render a daily operations report."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-daily-{user_id}.html"
    output_path = os.path.join(output_dir, filename)

    total_likes = 0
    total_comments = 0
    total_collects = 0
    for note in notes:
        if note.interact_info:
            total_likes += note.interact_info.liked_count
            total_comments += note.interact_info.comment_count
            total_collects += note.interact_info.collected_count

    sorted_notes = sorted(
        notes,
        key=lambda n: n.interact_info.liked_count if n.interact_info else 0,
        reverse=True,
    )[:5]

    render_report(
        "daily.html",
        {
            "total_notes": len(notes),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_collects": total_collects,
            "top_notes": sorted_notes,
        },
        output_path,
    )
    return output_path
