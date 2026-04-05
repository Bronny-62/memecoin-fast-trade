from __future__ import annotations

from typing import Any

from monitoring_service.settings import Settings, load_settings


def get_settings() -> Settings:
    return load_settings()


def build_proxy(settings: Settings) -> Any:
    if not (settings.proxy_type and settings.proxy_addr and settings.proxy_port):
        return None
    try:
        from python_socks import ProxyType

        proxy_type_map = {
            "socks5": ProxyType.SOCKS5,
            "socks4": ProxyType.SOCKS4,
            "http": ProxyType.HTTP,
        }
        key = settings.proxy_type.lower()
        if key not in proxy_type_map:
            print(f"未知的代理类型: {settings.proxy_type}，将直连")
            return None
        return (
            proxy_type_map[key],
            settings.proxy_addr,
            int(settings.proxy_port),
            False,
            settings.proxy_username or None,
            settings.proxy_password or None,
        )
    except ImportError:
        print("警告: python-socks 未安装，请运行: pip install python-socks[asyncio]")
        return None
    except Exception as exc:
        print(f"代理配置失败: {exc}")
        return None

