from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from botspot.core.bot_manager import BotManager
from calmlib.utils import setup_logger
from loguru import logger

from src._app import App
from src.router import router as main_router
from src.routers.admin import router as admin_router
from src.routers.checkins import router as checkins_router
from src.routers.group import router as group_router
from src.routers.registration import router as registration_router
from src.service_account.setup_command import router as service_account_router


def _startup_hooks(dp: Dispatcher, app: App) -> None:
    from src.db import Repo
    from src.scheduler_jobs import schedule_all_jobs
    from src.service_account.client import ServiceAccountClient, init_service_client

    @dp.startup()
    async def _on_startup() -> None:
        from botspot.utils.deps_getters import get_database

        db = get_database()
        repo = Repo(db)
        await repo.ensure_indexes()
        dp["repo"] = repo

        client: ServiceAccountClient | None = None
        if app.config.sleep_bot_service_api_id and app.config.sleep_bot_service_api_hash:
            client = init_service_client(app)
            try:
                await client.connect_if_authorized()
            except Exception as e:
                logger.warning(f"Service account not auto-connected: {e}")
        dp["service_client"] = client

        await schedule_all_jobs(repo, client)
        logger.info("Startup finished")


def main(debug: bool = False) -> None:
    setup_logger(logger, level="DEBUG" if debug else "INFO")

    dp = Dispatcher()
    dp.include_router(main_router)
    dp.include_router(admin_router)
    dp.include_router(registration_router)
    dp.include_router(checkins_router)
    dp.include_router(group_router)
    dp.include_router(service_account_router)

    app = App()
    dp["app"] = app

    bot = Bot(
        token=app.config.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    bm = BotManager(
        bot=bot,
        error_handler={"enabled": True},
        ask_user={"enabled": True},
        bot_commands_menu={"enabled": True},
        mongo_database={"enabled": True},
        event_scheduler={"enabled": True},
        user_data={"enabled": True},
    )
    bm.setup_dispatcher(dp)

    _startup_hooks(dp, app)

    dp.run_polling(bot)


if __name__ == "__main__":
    import argparse
    import os

    from dotenv import load_dotenv

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    dotenv_path = repo_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)

    debug = args.debug if args.debug else bool(os.getenv("DEBUG"))
    main(debug=debug)
