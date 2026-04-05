from __future__ import annotations

import asyncio

from telethon import TelegramClient

from monitoring_service.tools.common import build_proxy, get_settings


async def resolve_single_bot(client: TelegramClient, bot_name: str, username: str, bot_id: int) -> int | None:
    print(f"\n=== 解析 {bot_name} ===")
    resolved_id = None

    if username:
        print(f"方法1: 通过用户名解析 {username}")
        try:
            bot_by_username = await client.get_entity(username)
            print(f"[YES] 通过用户名成功解析: {bot_by_username.first_name} (ID: {bot_by_username.id})")
            await client.send_message(bot_by_username, "/start")
            print(f"[YES] 已发送 /start 消息给 {bot_name}")
            resolved_id = bot_by_username.id
        except Exception as exc:
            print(f"[NO] 通过用户名解析失败: {exc}")

    if bot_id and not resolved_id:
        print(f"方法2: 通过 ID 解析 {bot_id}")
        try:
            bot_by_id = await client.get_entity(bot_id)
            print(f"[YES] 通过 ID 成功解析: {bot_by_id.first_name}")
            resolved_id = bot_id
        except Exception as exc:
            print(f"[NO] 通过 ID 解析失败: {exc}")

    if not resolved_id and username:
        print(f"方法3: 搜索最近对话中的 {bot_name}")
        target_username = username.replace("@", "").lower()
        async for dialog in client.iter_dialogs(limit=50):
            if hasattr(dialog.entity, "bot") and dialog.entity.bot:
                if dialog.entity.username and dialog.entity.username.lower() == target_username:
                    print(f"[YES] 在对话中找到 {bot_name}: {dialog.entity.first_name}")
                    resolved_id = dialog.entity.id
                    break

    if resolved_id:
        print(f"[SUCCESS] {bot_name} 解析成功 (ID: {resolved_id})")
    else:
        print(f"[ERROR] {bot_name} 解析失败")
    return resolved_id


async def main() -> None:
    settings = get_settings()
    print("=== 机器人解析与缓存工具 ===")

    proxy = build_proxy(settings)
    if proxy:
        print(f"使用代理: {settings.proxy_type}://{settings.proxy_addr}:{settings.proxy_port}")
    else:
        print("未配置代理，将直连")

    client = TelegramClient("anon", settings.api_id, settings.api_hash, proxy=proxy, system_version="4.16.30-vxCUSTOM")
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("[NO] 未授权，请先运行: python -m monitoring_service.tools.telegram_auth")
            return

        me = await client.get_me()
        print(f"[YES] 已登录: {me.first_name}")

        resolved_bots = 0
        sigma_id = await resolve_single_bot(client, "SigmaBot", settings.sigma_bot_username, settings.sigma_bot_id)
        if sigma_id:
            resolved_bots += 1
        ave_id = await resolve_single_bot(client, "BasedBot", settings.based_bot_username, settings.based_bot_id)
        if ave_id:
            resolved_bots += 1

        print("\n=== 解析总结 ===")
        print(f"成功解析的机器人数量: {resolved_bots}/2")
        if resolved_bots == 2:
            print("[SUCCESS] 所有机器人都已成功解析和缓存。")
        elif resolved_bots == 1:
            print("[WARNING] 只有一个机器人解析成功，部分功能可能受限。")
        else:
            print("[ERROR] 没有机器人解析成功，请检查配置。")
            print("1. 确认你已在 Telegram 客户端与机器人建立对话")
            print("2. 检查机器人用户名和 ID 是否正确")
            print("3. 确认机器人仍然存在且可访问")
    except Exception as exc:
        print(f"[ERROR] 解析过程失败: {exc}")
        raise
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

