"""Config management commands."""

import typer
import yaml
from rednote_core.config import load_config

config_app = typer.Typer(help="配置管理", no_args_is_help=True)


@config_app.command("show")
def config_show():
    """显示当前配置."""
    config = load_config()
    print(yaml.dump(config, allow_unicode=True, default_flow_style=False))


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="配置键，如 client.proxy"),
    value: str = typer.Argument(..., help="配置值"),
):
    """设置配置项."""
    print(f"设置 {key} = {value}")
    print("请手动编辑 config/settings.yaml 修改配置")
