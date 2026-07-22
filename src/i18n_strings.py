"""App-specific i18n strings.

Registered at startup via botspot.i18n.register_strings. Language is auto-resolved
by botspot's I18nMiddleware from message.from_user.language_code (default "en",
"ru" when language_code starts with "ru"). Scheduler jobs call set_lang(user.lang)
manually before emitting.
"""

STRINGS: dict[str, dict[str, str]] = {
    # router.py
    "start_admin": {
        "en": (
            "Hi {name} 👋 — you're an <b>admin</b>.\n\n"
            "<b>Quickstart:</b>\n"
            "• /admin_new_challenge — create a challenge (here in DM)\n"
            "• in the group: /bind_here — bind the challenge\n"
            "• /admin_start &lt;code&gt; — go live\n\n"
            "<b>More:</b> /admin_list_challenges · /admin_finish · /help"
        ),
        "ru": (
            "Привет, {name} 👋 — ты <b>админ</b>.\n\n"
            "<b>Быстрый старт:</b>\n"
            "• /admin_new_challenge — создать челлендж (тут в DM)\n"
            "• в группе: /bind_here — привязать челлендж\n"
            "• /admin_start &lt;code&gt; — запустить\n\n"
            "<b>Ещё:</b> /admin_list_challenges · /admin_finish · /help"
        ),
    },
    "start_user": {
        "en": (
            "Hi {name}!\n\n"
            "<b>How to join:</b>\n"
            "• /join — pick your challenge (buttons)\n"
            "• follow the short setup wizard\n\n"
            "<b>How to participate:</b>\n"
            "• post 🎥 video notes (кружочки) in the challenge group\n"
            "• one at bedtime, one at wake-up → that's your check-in\n"
            "• 👍 on time / 🥱 late\n\n"
            "Type /help for more."
        ),
        "ru": (
            "Привет, {name}!\n\n"
            "<b>Как присоединиться:</b>\n"
            "• /join — выбрать челлендж (кнопки)\n"
            "• пройти короткий визард\n\n"
            "<b>Как участвовать:</b>\n"
            "• отправляй 🎥 кружочки в групповой чат челленджа\n"
            "• один перед сном, один при пробуждении → это чек-ин\n"
            "• 👍 вовремя / 🥱 поздно\n\n"
            "/help — подробнее."
        ),
    },
    "help": {
        "en": (
            "<b>{name}</b>\n\n"
            "<b>In the challenge group:</b>\n"
            "/join — enroll (I'll DM you the setup wizard)\n"
            "🎥 post a video note at bed and at wake — that's your check-in\n\n"
            "<b>In DM (settings &amp; private history):</b>\n"
            "/status — today's log, streak, deadlines\n"
            "/history — last 14 days\n"
            "/tighten_bed HH:MM — move bedtime earlier (never later)\n"
            "/tighten_wake HH:MM — move wake-up earlier\n"
            "/how_to_share_online — bonus 'last seen' setup\n\n"
            "<b>Admin (DM):</b>\n"
            "/admin_new_challenge — create a challenge\n"
            "/admin_list_challenges\n"
            "/admin_start &lt;code&gt; — activate a challenge\n"
            "/admin_finish &lt;code&gt;\n"
            "/bind_here &lt;code&gt; — bind the current group to a challenge (run in group)\n"
            "/setup_telethon — authorize the Telethon service account (bonus)"
        ),
        "ru": (
            "<b>{name}</b>\n\n"
            "<b>В групповом чате челленджа:</b>\n"
            "/join — присоединиться (визард придёт в ЛС)\n"
            "🎥 отправь кружочек перед сном и при пробуждении — это чек-ин\n\n"
            "<b>В ЛС (настройки и история):</b>\n"
            "/status — сегодняшний лог, серия, дедлайны\n"
            "/history — последние 14 дней\n"
            "/tighten_bed HH:MM — сдвинуть дедлайн сна раньше (только раньше)\n"
            "/tighten_wake HH:MM — сдвинуть дедлайн подъёма раньше\n"
            "/how_to_share_online — бонус «last seen»\n\n"
            "<b>Админ (ЛС):</b>\n"
            "/admin_new_challenge — создать челлендж\n"
            "/admin_list_challenges\n"
            "/admin_start &lt;code&gt; — активировать челлендж\n"
            "/admin_finish &lt;code&gt;\n"
            "/bind_here &lt;code&gt; — привязать текущую группу (запускать в группе)\n"
            "/setup_telethon — авторизовать сервис-аккаунт Telethon (бонус)"
        ),
    },
    # registration.py
    "ask_tz_method": {
        "en": "How should I figure out your timezone?",
        "ru": "Как определить твой часовой пояс?",
    },
    "ask_tz_current": {
        "en": "🕐 Send current local time",
        "ru": "🕐 Прислать текущее локальное время",
    },
    "ask_tz_manual": {
        "en": "✏️ Type Olson name (e.g. Europe/Zurich)",
        "ru": "✏️ Ввести Olson-имя (напр. Europe/Zurich)",
    },
    "ask_tz_current_prompt": {
        "en": "Your current local time as HH:MM:",
        "ru": "Твоё текущее локальное время в формате HH:MM:",
    },
    "tz_inferred": {
        "en": "Inferred timezone: <code>{tz}</code>",
        "ru": "Определил часовой пояс: <code>{tz}</code>",
    },
    "tz_infer_failed": {
        "en": "Could not infer timezone from that.",
        "ru": "Не удалось определить часовой пояс.",
    },
    "ask_tz_olson_prompt": {
        "en": "Enter Olson name, e.g. Europe/Zurich:",
        "ru": "Введи Olson-имя, напр. Europe/Zurich:",
    },
    "tz_unknown": {
        "en": "That's not a known timezone.",
        "ru": "Такой часовой пояс неизвестен.",
    },
    "ask_bed_manual": {
        "en": "Bedtime deadline (HH:MM local):",
        "ru": "Дедлайн сна (HH:MM, локальное время):",
    },
    "ask_wake_manual": {
        "en": "Wake-up deadline (HH:MM local):",
        "ru": "Дедлайн подъёма (HH:MM, локальное время):",
    },
    "parse_failed": {
        "en": "Couldn't parse those.",
        "ru": "Не смог распарсить.",
    },
    "ask_usual_bed": {
        "en": (
            "What time do you usually go to bed lately (HH:MM)? "
            "Reply <code>varies</code> if it's all over the place."
        ),
        "ru": (
            "Во сколько ты обычно ложишься последнее время (HH:MM)? "
            "Ответь <code>varies</code>, если по-разному."
        ),
    },
    "usual_varies_defaults": {
        "en": "Using sensible midnight-ish defaults (bed 23:30, wake 07:30).",
        "ru": "Беру дефолты около полуночи (сон 23:30, подъём 07:30).",
    },
    "ask_usual_wake": {
        "en": "And your usual wake-up time (HH:MM)?",
        "ru": "И обычное время подъёма (HH:MM)?",
    },
    "parse_failed_abort": {
        "en": "Couldn't parse that. Aborting.",
        "ru": "Не смог распарсить. Отмена.",
    },
    "ask_difficulty": {
        "en": "How much earlier should your deadline be?",
        "ru": "Насколько сдвинуть дедлайн раньше?",
    },
    "difficulty_light": {
        "en": "Light (−30 min)",
        "ru": "Лёгкий (−30 мин)",
    },
    "difficulty_medium": {
        "en": "Medium (−1h) ⭐ recommended",
        "ru": "Средний (−1ч) ⭐ рекомендуется",
    },
    "difficulty_hard": {
        "en": "Hard (−2h)",
        "ru": "Сложный (−2ч)",
    },
    "difficulty_manual": {
        "en": "Manual",
        "ru": "Вручную",
    },
    "already_registered": {
        "en": "You're already registered in this challenge.",
        "ru": "Ты уже зарегистрирован в этом челлендже.",
    },
    "ask_flow": {
        "en": "How do you want to set your deadlines?",
        "ru": "Как задать дедлайны?",
    },
    "flow_guided": {
        "en": "Guided (recommended)",
        "ru": "С подсказками (рекомендуется)",
    },
    "flow_manual": {
        "en": "Manual — I know my times",
        "ru": "Вручную — знаю свои времена",
    },
    "flow_defaults": {
        "en": "Use sensible defaults (23:30 / 07:30)",
        "ru": "Дефолты (23:30 / 07:30)",
    },
    "wizard_done": {
        "en": (
            "🎯 You're in.\n"
            "Timezone: <code>{tz}</code>\n"
            "Bedtime deadline: <b>{bed}</b>\n"
            "Wake-up deadline: <b>{wake}</b>\n\n"
            "Now send 🎥 <b>video notes</b> (кружочки) in the challenge group — "
            "one when you're in bed, one when you wake up. "
            "Use /tighten_bed or /tighten_wake to move a deadline earlier."
        ),
        "ru": (
            "🎯 Готово.\n"
            "Часовой пояс: <code>{tz}</code>\n"
            "Дедлайн сна: <b>{bed}</b>\n"
            "Дедлайн подъёма: <b>{wake}</b>\n\n"
            "Теперь отправляй 🎥 <b>кружочки</b> в группу челленджа — "
            "один когда в кровати, один после пробуждения. "
            "Используй /tighten_bed или /tighten_wake, чтобы сдвинуть дедлайн раньше."
        ),
    },
    "join_no_challenge_with_code": {
        "en": "No active challenge with code <code>{code}</code>.",
        "ru": "Нет активного челленджа с кодом <code>{code}</code>.",
    },
    "join_no_group_member": {
        "en": (
            "I don't see you in any active challenge group yet.\n"
            "Join the challenge group first, then come back and run /join here "
            "(or /join inside the group)."
        ),
        "ru": (
            "Я не вижу тебя ни в одной активной группе челленджа.\n"
            "Сначала зайди в группу челленджа, потом запусти /join тут "
            "(или /join прямо в группе)."
        ),
    },
    "join_pick": {
        "en": "Pick a challenge to join:",
        "ru": "Выбери челлендж:",
    },
    "join_button": {
        "en": "Join {name}",
        "ru": "Присоединиться: {name}",
    },
    "join_no_active_callback": {
        "en": "No active challenge {code}",
        "ru": "Нет активного челленджа {code}",
    },
    "join_starting_setup": {
        "en": "Starting setup for <b>{name}</b> (<code>{code}</code>)…",
        "ru": "Запускаю настройку для <b>{name}</b> (<code>{code}</code>)…",
    },
    # group.py
    "group_no_active": {
        "en": (
            "No active challenge is bound to this group. "
            "An admin needs to /bind_here &lt;code&gt; first."
        ),
        "ru": (
            "К этой группе не привязан активный челлендж. "
            "Админу нужно сначала /bind_here &lt;code&gt;."
        ),
    },
    "group_wrong_code": {
        "en": "This group hosts <code>{code}</code>; ignoring <code>{wrong}</code>.",
        "ru": "В этой группе челлендж <code>{code}</code>; игнорирую <code>{wrong}</code>.",
    },
    "group_dm_kickoff": {
        "en": "👋 Kicking off setup for <b>{name}</b> (<code>{code}</code>).",
        "ru": "👋 Начинаю настройку для <b>{name}</b> (<code>{code}</code>).",
    },
    "group_dm_blocked_button": {
        "en": "Start chat with the bot",
        "ru": "Начать чат с ботом",
    },
    "group_dm_blocked_msg": {
        "en": "@{username} — press the button, hit Start, then run /join here again.",
        "ru": "@{username} — нажми кнопку, Start, потом снова /join тут.",
    },
    "group_setup_cancelled": {
        "en": "@{username} — setup was cancelled. Run /join again when you're ready.",
        "ru": "@{username} — настройка отменена. Запусти /join снова, когда будешь готов.",
    },
    "group_user_joined": {
        "en": "✅ <b>{name}</b> joined. Bed {bed} · Wake {wake}.",
        "ru": "✅ <b>{name}</b> присоединился. Сон {bed} · Подъём {wake}.",
    },
    # admin.py
    "ask_start_date": {
        "en": "Start date?",
        "ru": "Дата старта?",
    },
    "ask_start_today": {
        "en": "Today ({date})",
        "ru": "Сегодня ({date})",
    },
    "ask_start_tomorrow": {
        "en": "Tomorrow ({date})",
        "ru": "Завтра ({date})",
    },
    "ask_start_custom": {
        "en": "Custom date (YYYY-MM-DD)",
        "ru": "Другая дата (YYYY-MM-DD)",
    },
    "ask_start_custom_prompt": {
        "en": "Enter start date (YYYY-MM-DD):",
        "ru": "Введи дату старта (YYYY-MM-DD):",
    },
    "ask_end_date": {
        "en": "End date?",
        "ru": "Дата окончания?",
    },
    "ask_end_1w": {
        "en": "1 week ({date})",
        "ru": "1 неделя ({date})",
    },
    "ask_end_2w": {
        "en": "2 weeks ({date})",
        "ru": "2 недели ({date})",
    },
    "ask_end_3w": {
        "en": "3 weeks ({date})",
        "ru": "3 недели ({date})",
    },
    "ask_end_custom": {
        "en": "Custom date",
        "ru": "Другая дата",
    },
    "ask_end_none": {
        "en": "No end date",
        "ru": "Без даты окончания",
    },
    "ask_end_custom_prompt": {
        "en": "Enter end date (YYYY-MM-DD):",
        "ru": "Введи дату окончания (YYYY-MM-DD):",
    },
    "ask_challenge_code": {
        "en": "Challenge code (short, unique, e.g. sleep-apr26):",
        "ru": "Код челленджа (короткий, уникальный, напр. sleep-apr26):",
    },
    "code_exists": {
        "en": "Code <code>{code}</code> already exists.",
        "ru": "Код <code>{code}</code> уже существует.",
    },
    "ask_challenge_name": {
        "en": "Human-readable name:",
        "ru": "Человекочитаемое имя:",
    },
    "challenge_created": {
        "en": (
            "Created draft challenge <code>{code}</code> · {dates}.\n"
            "In the target group, run <code>/bind_here</code> "
            "(no args — I'll show a button) to bind it. "
            "Then <code>/admin_start {code}</code> to activate."
        ),
        "ru": (
            "Создан черновик челленджа <code>{code}</code> · {dates}.\n"
            "В нужной группе запусти <code>/bind_here</code> "
            "(без аргументов — покажу кнопку). "
            "Потом <code>/admin_start {code}</code> для активации."
        ),
    },
    "no_challenges_yet": {
        "en": "No challenges yet.",
        "ru": "Пока нет челленджей.",
    },
    "admin_start_usage": {
        "en": "Usage: /admin_start &lt;code&gt;",
        "ru": "Использование: /admin_start &lt;code&gt;",
    },
    "admin_no_challenge": {
        "en": "No challenge <code>{code}</code>.",
        "ru": "Нет челленджа <code>{code}</code>.",
    },
    "admin_activated": {
        "en": "Activated <code>{code}</code>.",
        "ru": "Активирован <code>{code}</code>.",
    },
    "group_announce_live": {
        "en": (
            "🌙 Challenge <b>{name}</b> is live.\n"
            "Type <code>/join</code> right here to enroll — "
            "I'll DM you a short setup wizard."
        ),
        "ru": (
            "🌙 Челлендж <b>{name}</b> запущен.\n"
            "Пиши <code>/join</code> прямо тут — "
            "я пришлю короткий визард в ЛС."
        ),
    },
    "admin_finished": {
        "en": "Finished <code>{code}</code>.",
        "ru": "Завершён <code>{code}</code>.",
    },
    "bind_bound": {
        "en": "Bound <code>{code}</code> to this chat (id={chat_id}).",
        "ru": "Привязал <code>{code}</code> к этому чату (id={chat_id}).",
    },
    "bind_no_unbound": {
        "en": "No unbound challenges. Create one in DM with /admin_new_challenge.",
        "ru": "Нет непривязанных челленджей. Создай в ЛС через /admin_new_challenge.",
    },
    "bind_pick": {
        "en": "Pick a challenge to bind to this group:",
        "ru": "Выбери челлендж для привязки к группе:",
    },
    "bind_cb_no_challenge": {
        "en": "No challenge {code}",
        "ru": "Нет челленджа {code}",
    },
    "bind_cb_bound_elsewhere": {
        "en": "{code} is already bound elsewhere.",
        "ru": "{code} уже привязан к другой группе.",
    },
    "bind_cb_success_answer": {
        "en": "Bound {code} here.",
        "ru": "Привязал {code} сюда.",
    },
    "bind_cb_success_edit": {
        "en": "✅ Bound <code>{code}</code> to this chat (id={chat_id}).",
        "ru": "✅ Привязал <code>{code}</code> к этому чату (id={chat_id}).",
    },
    # settings.py
    "tighten_bed_usage": {
        "en": "Usage: /tighten_bed HH:MM",
        "ru": "Использование: /tighten_bed HH:MM",
    },
    "tighten_wake_usage": {
        "en": "Usage: /tighten_wake HH:MM",
        "ru": "Использование: /tighten_wake HH:MM",
    },
    "not_in_active": {
        "en": "You're not in any active challenge.",
        "ru": "Ты не участвуешь в активном челлендже.",
    },
    "tighten_rejected": {
        "en": (
            "Deadlines can only be tightened, never relaxed. "
            "Current: {current}."
        ),
        "ru": (
            "Дедлайны можно только ужесточать, не смягчать. "
            "Текущий: {current}."
        ),
    },
    "bedtime_updated": {
        "en": "Bedtime deadline now {time}.",
        "ru": "Дедлайн сна теперь {time}.",
    },
    "wake_updated": {
        "en": "Wake deadline now {time}.",
        "ru": "Дедлайн подъёма теперь {time}.",
    },
    "status_body": {
        "en": (
            "<b>Today</b> ({date})\n"
            "Bed: {bed}\nWake: {wake}\n"
            "Seen online: {online}\n"
            "Bedtime deadline: {bed_deadline} · Wake deadline: {wake_deadline}\n"
            "Streak: <b>{streak}</b>"
        ),
        "ru": (
            "<b>Сегодня</b> ({date})\n"
            "Сон: {bed}\nПодъём: {wake}\n"
            "Онлайн: {online}\n"
            "Дедлайн сна: {bed_deadline} · Дедлайн подъёма: {wake_deadline}\n"
            "Серия: <b>{streak}</b>"
        ),
    },
    "no_logs": {
        "en": "No logs yet.",
        "ru": "Пока нет записей.",
    },
    "how_to_share_online": {
        "en": (
            "<b>Bonus: share your online status</b>\n\n"
            "1. Add the challenge service account to your Telegram contacts "
            "(phone +41 77 218 4188).\n"
            "2. Telegram → Settings → Privacy &amp; Security → Last Seen &amp; Online → "
            "My Contacts (or add a specific exception).\n"
            "3. I'll use 'last seen' as a fallback hint in /status.\n\n"
            "Skip if you'd rather not — scoring still works off your видео-заметки."
        ),
        "ru": (
            "<b>Бонус: делиться онлайн-статусом</b>\n\n"
            "1. Добавь сервис-аккаунт челленджа в контакты Telegram "
            "(номер +41 77 218 4188).\n"
            "2. Telegram → Настройки → Конфиденциальность → Время захода → "
            "Мои контакты (или добавь исключение).\n"
            "3. Я буду использовать «last seen» как запасной сигнал в /status.\n\n"
            "Можешь пропустить — скоринг работает и по видео-заметкам."
        ),
    },
    # scheduler_jobs.py
    "remind_bed": {
        "en": (
            "⏰ Bedtime deadline in 30 min ({deadline}). "
            "Send a message or 🎥 video note when you're in bed."
        ),
        "ru": (
            "⏰ Дедлайн сна через 30 минут ({deadline}). "
            "Пришли сообщение или 🎥 кружочек, когда будешь в кровати."
        ),
    },
    "remind_wake": {
        "en": "⏰ Wake-up deadline in 30 min ({deadline}).",
        "ru": "⏰ Дедлайн подъёма через 30 минут ({deadline}).",
    },
    "daily_group_stats": {
        "en": (
            "🌅 {name} · {date}\n"
            "✅ {ones} on-time · ⚠️ {halves} half · ❌ {zeros} missed"
        ),
        "ru": (
            "🌅 {name} · {date}\n"
            "✅ {ones} вовремя · ⚠️ {halves} частично · ❌ {zeros} пропуск"
        ),
    },
    "weekly_leaderboard_header": {
        "en": "🏆 Weekly leaderboard · {name}",
        "ru": "🏆 Лидерборд недели · {name}",
    },
    "weekly_leaderboard_row": {
        "en": "{rank}. {name} — {total} pts · streak {streak}",
        "ru": "{rank}. {name} — {total} очков · серия {streak}",
    },
}
