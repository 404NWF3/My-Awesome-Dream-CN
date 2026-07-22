"""RedNote CLI entry point."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="rednote",
    help="小红书 (Xiaohongshu / RedNote) 数据采集 CLI",
    no_args_is_help=True,
)

# Register subcommands
from rednote.commands.login_cmd import login_app
app.add_typer(login_app, name="login", help="扫码登录")

from rednote.commands.scrape import scrape_app
app.add_typer(scrape_app, name="scrape", help="数据采集")

from rednote.commands.config_cmd import config_app
app.add_typer(config_app, name="config", help="配置管理")

from rednote.commands.report_cmd import report_app
app.add_typer(report_app, name="report", help="报告生成")
