from __future__ import annotations

import asyncio

from telethon import TelegramClient

from monitoring_service.tools.common import build_proxy, get_settings


async def main() -> None:
    settings = get_settings()

    print("=== Telegram 账户授权工具 ===")
    print(f"API ID: {settings.api_id}")
    print(f"API Hash: {settings.api_hash[:8]}...")
    print(f"SigmaBot ID: {settings.sigma_bot_id}")
    print(f"BasedBot ID: {settings.based_bot_id}")

    proxy = build_proxy(settings)
    if proxy:
        print(f"使用代理: {settings.proxy_type}://{settings.proxy_addr}:{settings.proxy_port}")
    else:
        print("未配置代理，将直连")
    print()

    client = TelegramClient("anon", settings.api_id, settings.api_hash, proxy=proxy, system_version="4.16.30-vxCUSTOM")
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("需要授权登录...")
            phone = input("请输入你的 Telegram 手机号（包含国家代码，例如 +86138...）: ")
            await client.send_code_request(phone)
            code = input("请输入收到的验证码: ")
            try:
                await client.sign_in(phone, code)
            except Exception as exc:
                if "Two-step verification" in str(exc) or "password" in str(exc).lower():
                    password = input("请输入你的两步验证密码: ")
                    await client.sign_in(password=password)
                else:
                    raise

        me = await client.get_me()
        print(f"[YES] 登录成功！用户: {me.first_name} (@{me.username or 'N/A'})")

        bots_resolved = 0
        if settings.sigma_bot_id:
            print(f"\n--- 测试 SigmaBot (ID: {settings.sigma_bot_id}) ---")
            try:
                sigma_bot = await client.get_entity(settings.sigma_bot_id)
                print(f"[YES] 成功解析 SigmaBot: {sigma_bot.first_name} (ID: {sigma_bot.id})")
                await client.send_message(sigma_bot, "/start")
                print("[YES] 已发送 /start 消息给 SigmaBot")
                bots_resolved += 1
            except Exception as exc:
                print(f"[NO] 无法解析 SigmaBot ID {settings.sigma_bot_id}: {exc}")

        if settings.based_bot_id:
            print(f"\n--- 测试 BasedBot (ID: {settings.based_bot_id}) ---")
            try:
                ave_bot = await client.get_entity(settings.based_bot_id)
                print(f"[YES] 成功解析 BasedBot: {ave_bot.first_name} (ID: {ave_bot.id})")
                await client.send_message(ave_bot, "/start")
                print("[YES] 已发送 /start 消息给 BasedBot")
                bots_resolved += 1
            except Exception as exc:
                print(f"[NO] 无法解析 BasedBot ID {settings.based_bot_id}: {exc}")

        print("\n=== 授权总结 ===")
        print(f"成功解析的机器人数量: {bots_resolved}/2")
        if bots_resolved == 2:
            print("[SUCCESS] 所有机器人都已成功连接，系统可以正常运行。")
        elif bots_resolved == 1:
            print("[WARNING] 只有一个机器人连接成功，部分功能可能受限。")
        else:
            print("[ERROR] 没有机器人连接成功，请检查配置和网络连接。")
        print("\n[SUCCESS] 授权完成，现在可以启动主服务。")
    except Exception as exc:
        print(f"[NO] 授权失败: {exc}")
        raise
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

