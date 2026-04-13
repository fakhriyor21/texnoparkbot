"""
Guliston yoshlar texnoparki — targibot boti (aiogram 3).
Ketma-ketlik: OTM tanlash → ism+familiya (bitta xabar) → telefon → muammo.
"""
from __future__ import annotations

import html
import logging
import os
import re
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputProfilePhotoStatic,
    Message,
)
from dotenv import load_dotenv

import db

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
_ADMIN_RAW = os.environ.get("ADMIN_IDS", "").strip()
ADMIN_IDS: set[int] = set()
for part in _ADMIN_RAW.replace(" ", "").split(","):
    if part.isdigit():
        ADMIN_IDS.add(int(part))


class Survey(StatesGroup):
    otm = State()
    full_name = State()
    phone = State()
    problem = State()


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in ADMIN_IDS


# Start bosilmasdan chat tepasida ko‘rinadigan qisqa tavsif (Telegram: max ~120 belgi).
BOT_SHORT_DESCRIPTION = (
    "Guliston Yoshlar Texnoparki: OTM tanlash, ism+familiya, telefon, muammo → 2 xonali kod. "
    "/start"
)

# Bot profilidagi “About” / to‘liqroq tavsif (Telegram: max ~512 belgi).
BOT_ABOUT_DESCRIPTION = (
    "Bu bot Guliston Yoshlar Texnoparki jamoasi uchun: universitet va tadbirlarda "
    "ishtirokchilardan qisqa ma’lumot olish.\n\n"
    "Nima qiladi?\n"
    "• Avval OTM (universitet) tanlaysiz, keyin ism+familiya, telefon va muammo.\n"
    "• Startap tushunchasiga kirish va g‘oya bosqichini tushunish uchun.\n"
    "• Topshirgach sizga 2 xonali kod beriladi (masalan, charxpalak).\n"
    "• Ma’lumot texnopark adminiga boradi; ular qabul yoki rad qiladi.\n\n"
    "/start — boshlash · /yangi — qayta topshirish · /cancel — bekor."
)


# OTM slug → bazaga yoziladigan rasmiy nom
OTM_BY_SLUG: dict[str, str] = {
    "gdu": "Guliston davlat universiteti",
    "gdpi": "Guliston davlat pedagogika instituti",
    "buxfi": "Buxoro fan va innovatsiyalar universiteti",
}

OTM_SLUG_EMOJI: dict[str, str] = {
    "gdu": "🎓",
    "gdpi": "📚",
    "buxfi": "🔬",
}


def otm_reply_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎓 Guliston davlat universiteti",
                    callback_data="otm:gdu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Guliston davlat pedagogika instituti",
                    callback_data="otm:gdpi",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔬 Buxoro fan va innovatsiyalar universiteti",
                    callback_data="otm:buxfi",
                )
            ],
        ]
    )


WELCOME_INTRO = (
    "🌟 *Salom, kelajak tuzuvchisi!*\n\n"
    "Biz — *Guliston yoshlar texnoparki* jamoasi. 🚀✨\n"
    "Bugun *startap* va *“muammo → g‘oya”* zanjirini birga o‘ylaymiz.\n\n"
    "Har bir katta g‘oya oddiy savoldan boshlanadi: "
    "*“Atrofimda nima yaxshilanishi kerak?”*\n\n"
    "🎯 *Birinchi qadam:* pastdagi menyudan *OTM*ingizni tanlang.\n"
    "_Emojili tugmalar — 🎓 📚 🔬 ; stickerni emas, aynan universitet tugmasini bosing_ 😉"
)


def build_admin_notification_html(
    row_id: int,
    code: str,
    otm: str,
    ism: str,
    familya: str,
    phone: str,
    username: str | None,
    user_id: int,
    problem: str,
) -> str:
    """Admin uchun: muammo kodi va muammo matni aniq ajratilgan HTML."""
    esc = html.escape
    prob_block = esc(problem)
    if username:
        uname_line = f"✉️ @{esc(username)} · Telegram ID: <code>{user_id}</code>"
    else:
        uname_line = f"✉️ <i>username yo‘q</i> · Telegram ID: <code>{user_id}</code>"
    otm_disp = esc(otm) if otm else "—"
    return (
        "🚀 <b>Guliston Yoshlar Texnoparki</b>\n"
        "<i>Yangi topshiruv · ariza radarida</i>\n\n"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"┃ 🎫 <b>MUAMMO KODI</b> <i>(charxpalak uchun)</i>\n"
        f"┃    <code>{esc(code)}</code>\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <b>MUAMMO MATNI</b> <i>(ishtirokchi yozgan)</i>\n"
        f"<pre>{prob_block}</pre>\n\n"
        "──────── <b>Kontakt</b> ────────\n"
        f"🆔 Ariza: <code>#{row_id}</code>\n"
        f"🏛 <b>OTM:</b> {otm_disp}\n"
        f"👤 {esc(ism)} {esc(familya)}\n"
        f"📞 <code>{esc(phone)}</code>\n"
        f"{uname_line}"
    )


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("registered_session"):
        await message.answer(
            "🔁 Siz allaqachon *texnopark radarida* qayd etilgansiz.\n"
            "Yana topshirish uchun */yangi* buyrug‘ini bosing — yangi sessiya ochiladi.",
            parse_mode="Markdown",
        )
        return
    await state.set_state(Survey.otm)
    await state.set_data({})
    await message.answer(
        WELCOME_INTRO,
        parse_mode="Markdown",
        reply_markup=otm_reply_markup(),
    )


@router.message(Command("yangi"))
async def cmd_yangi(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Survey.otm)
    await state.set_data({})
    await message.answer(
        "🔄 *Yangi sessiya!* 🎊 Oldingi qog‘oz uchdi — keling, qaytadan boshlaylik.\n\n"
        + WELCOME_INTRO,
        parse_mode="Markdown",
        reply_markup=otm_reply_markup(),
    )


@router.message(Command("cancel"), StateFilter(Survey))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🙌 Jarayon bekor qilindi. Qayta boshlash uchun */start* — biz har doim shu yerdamiz.",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("otm:"), StateFilter(Survey.otm))
async def on_otm_chosen(query: CallbackQuery, state: FSMContext) -> None:
    if not query.data or not query.message:
        return
    slug = query.data.removeprefix("otm:")
    label = OTM_BY_SLUG.get(slug)
    if not label:
        await query.answer("Noto‘g‘ri tanlov", show_alert=True)
        return
    await query.answer(f"{OTM_SLUG_EMOJI.get(slug, '🏛')} Tanlandi!")
    await state.update_data(otm=label)
    await state.set_state(Survey.full_name)
    em = OTM_SLUG_EMOJI.get(slug, "🏛")
    try:
        await query.message.edit_text(
            f"{em} <b>OTM tanlandi:</b> {html.escape(label)}",
            parse_mode="HTML",
        )
    except Exception:
        await query.message.answer(
            f"{em} <b>OTM tanlandi:</b> {html.escape(label)}",
            parse_mode="HTML",
        )
    await query.message.answer(
        "📝 Endi *ism va familyangizni bir qatorda* yuboring.\n"
        "Masalan: `Ali Karimov` yoki `Madina Tosheva Qodirova`\n\n"
        "✨ _Birinchi so‘z — ism, qolgani — familiya_",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("otm:"))
async def on_otm_stale(query: CallbackQuery) -> None:
    await query.answer(
        "⏳ Bu menyu eskirgan. /start yoki /yangi dan foydalaning.",
        show_alert=True,
    )


@router.message(StateFilter(Survey.otm), F.text)
async def on_otm_text_instead_of_button(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        return
    await message.answer(
        "👆 Iltimos, *pastdagi tugmalar* orqali OTM ni tanlang — "
        "🎓 📚 🔬 emojili variantlar.\n"
        "Stickerni emas, aynan *universitet* tugmasini bosing 😉",
        parse_mode="Markdown",
        reply_markup=otm_reply_markup(),
    )


@router.message(StateFilter(Survey.full_name), F.text)
async def on_full_name(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        return
    raw = (message.text or "").strip()
    parts = raw.split(None, 1)
    if len(parts) < 2:
        await message.answer(
            "✋ Iltimos, *ism va familiyani bir qatorda* yozing — ikkita qism bo‘lsin.\n"
            "Masalan: `Javohir Karimov`",
            parse_mode="Markdown",
        )
        return
    ism, familya = parts[0].strip(), parts[1].strip()
    if len(ism) < 2 or len(familya) < 2:
        await message.answer(
            "🙂 Ism yoki familiya juda qisqa. *To‘liqroq* yozing — masalan: `Ali Valiyev`",
            parse_mode="Markdown",
        )
        return
    await state.update_data(ism=ism, familya=familya)
    await state.set_state(Survey.phone)
    await message.answer(
        "📱 *Aloqa uchun raqamingiz* kerak — keyin sizga yangilik yoki sovg‘a "
        "yetkazishimiz mumkin. 📞✨\n"
        "Masalan: `+998901234567` yoki `901234567`",
        parse_mode="Markdown",
    )


@router.message(StateFilter(Survey.phone), F.text)
async def on_phone(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        return
    t = (message.text or "").strip().replace(" ", "")
    digits = "".join(c for c in t if c.isdigit())
    if len(digits) < 9:
        await message.answer(
            "Raqam to'liq emas. Iltimos, to'g'ri telefon raqamini yuboring."
        )
        return
    await state.update_data(phone=t)
    await state.set_state(Survey.problem)
    await message.answer(
        "🧩 *Oxirgi bosqich — “muammo ovlashi”!*\n\n"
        "*Global yoki sizga yaqin* bir muammoni qisqa yozing: transport, ta‘lim, "
        "ekologiya, sog‘liq, jamiyat, texnologiya…\n\n"
        "_G‘oya shu yerda tug‘iladi: muammo ko‘rganingizda — yechim izlash boshlanadi._",
        parse_mode="Markdown",
    )


@router.message(StateFilter(Survey.problem), F.text)
async def on_problem(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        return
    problem = (message.text or "").strip()
    if len(problem) < 10:
        await message.answer(
            "✏️ Bir oz batafsilroq yozing — kamida *10 ta belgi*. "
            "Qanchalik aniq bo‘lsa, jamoamiz shunchalik yaxshi tushunadi.",
            parse_mode="Markdown",
        )
        return

    u = message.from_user
    if not u:
        return
    data = await state.get_data()
    otm = data.get("otm", "") or ""
    ism = data.get("ism", "")
    familya = data.get("familya", "")
    phone = data.get("phone", "")

    row_id, code = await db.add_submission(
        telegram_user_id=u.id,
        username=u.username,
        otm=otm,
        ism=ism,
        familya=familya,
        phone=phone,
        problem=problem,
    )

    await state.update_data(registered_session=True)
    await state.set_state(None)

    await message.answer(
        "🎉 *Tabriklaymiz — siz radarga chiqdingiz!*\n\n"
        "Ma'lumotlaringiz *texnopark jamoasiga* yo‘llandi.\n\n"
        f"🎫 *Sizning muammo kodingiz:* `{code}`\n"
        "_Bu kod charxpalak yoki o‘yinlar uchun — uni saqlab qoling._\n\n"
        "Tez orada ko‘rib chiqamiz. *G‘oyalaringiz biz uchun qimmatli.* ✨",
        parse_mode="Markdown",
    )

    if ADMIN_IDS:
        admin_text = build_admin_notification_html(
            row_id=row_id,
            code=code,
            otm=otm,
            ism=ism,
            familya=familya,
            phone=phone,
            username=u.username,
            user_id=u.id,
            problem=problem,
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Qabul qilish",
                        callback_data=f"acc:{row_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Rad etish",
                        callback_data=f"rej:{row_id}",
                    ),
                ]
            ]
        )
        bot = message.bot
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(
                    aid,
                    admin_text,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            except Exception as e:
                log.warning("Admin %s ga yuborib bo'lmadi: %s", aid, e)


@router.message(Command("kutilayotgan"))
async def cmd_kutilayotgan(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("Sizda admin huquqi yo'q.")
        return
    pending = await db.list_pending()
    if not pending:
        await message.answer(
            "✨ <b>Radar toza!</b> Hozircha kutilayotgan ariza yo‘q — "
            "yoki hammasi allaqachon qayta ishlangan.",
            parse_mode="HTML",
        )
        return
    chunks = []
    for p in pending[:50]:
        prob_short = (p["problem"] or "")[:80].replace("\n", " ")
        if len(p["problem"] or "") > 80:
            prob_short += "…"
        otm_short = (p.get("otm") or "")[:40]
        if len(p.get("otm") or "") > 40:
            otm_short += "…"
        line = (
            f"🎫 <code>{html.escape(p['code'])}</code> · "
            f"#{p['id']} · {html.escape(p['ism'])} {html.escape(p['familya'])}\n"
            f"   🏛 {html.escape(otm_short) if otm_short else '—'}\n"
            f"   💬 {html.escape(prob_short)}"
        )
        chunks.append(line)
    await message.answer(
        "📋 <b>Kutilayotgan arizalar</b> <i>(birinchi 50)</i>\n\n" + "\n\n".join(chunks),
        parse_mode="HTML",
    )


_cb_re = re.compile(r"^(acc|rej):(\d+)$")


@router.callback_query(F.data.regexp(_cb_re))
async def on_admin_callback(query: CallbackQuery) -> None:
    if not query.from_user or not is_admin(query.from_user.id):
        await query.answer("Ruxsat yo'q.", show_alert=True)
        return
    if not query.data or not query.message:
        return
    m = _cb_re.match(query.data)
    if not m:
        return
    action, sid_s = m.group(1), m.group(2)
    sid = int(sid_s)
    await query.answer()

    rec = await db.get_by_id(sid)
    if not rec:
        await query.message.edit_text("Yozuv topilmadi.")
        return

    msg = query.message
    base_html = getattr(msg, "html_text", None) or html.escape(msg.text or "")

    if action == "acc":
        ok = await db.set_status(sid, "accepted")
        if not ok:
            await query.message.edit_text("Bu ariza allaqachon qayta ishlangan.")
            return
        await query.message.edit_text(
            base_html + "\n\n✅ Qabul qilindi.",
            parse_mode="HTML",
        )
        try:
            await query.bot.send_message(
                rec["telegram_user_id"],
                (
                    "🎉 *Rasmiy qabul!* Guliston yoshlar texnoparki "
                    "arizangizni *radariga oldi*.\n\n"
                    f"🎫 *Muammo kodingiz:* `{rec['code']}`\n"
                    "Keyingi qadamlar bo‘yicha jamoamiz *siz bilan bog‘lanishi mumkin*."
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            log.warning("Foydalanuvchiga xabar yuborib bo'lmadi: %s", e)

    elif action == "rej":
        ok = await db.set_status(sid, "rejected")
        if not ok:
            await query.message.edit_text("Bu ariza allaqachon qayta ishlangan.")
            return
        await query.message.edit_text(
            base_html + "\n\n❌ Rad etildi.",
            parse_mode="HTML",
        )
        try:
            await query.bot.send_message(
                rec["telegram_user_id"],
                (
                    "📋 Arizangiz *ko‘rib chiqildi*. Hozircha radarda joy "
                    "bo‘lmadi — lekin bu *“yo‘q” emas, “hozircha”* degani.\n\n"
                    "Batafsil uchun texnopark bilan bog‘laning — yana ko‘ramiz! 💪"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            log.warning("Foydalanuvchiga xabar yuborib bo'lmadi: %s", e)


async def main() -> None:
    await db.init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logo_path = Path(__file__).resolve().parent / "assets" / "bot_logo.png"

    async def on_startup() -> None:
        # Start bosilmasdan oldin chatda / profilda ko‘rinadigan tavsiflar
        try:
            short = BOT_SHORT_DESCRIPTION.strip()
            about = BOT_ABOUT_DESCRIPTION.strip()
            if len(short) > 120:
                short = short[:117] + "..."
                log.warning("Qisqa tavsif 120 belgiga qisqartirildi.")
            if len(about) > 512:
                about = about[:509] + "..."
                log.warning("To'liq tavsif 512 belgiga qisqartirildi.")
            await bot.set_my_short_description(short_description=short)
            await bot.set_my_description(description=about)
            log.info("Bot qisqa va to'liq tavsiflari yangilandi.")
        except Exception as e:
            log.warning("Bot tavsiflarini o'rnatib bo'lmadi: %s", e)

        if logo_path.is_file():
            try:
                await bot.set_my_profile_photo(
                    photo=InputProfilePhotoStatic(photo=FSInputFile(logo_path)),
                )
                log.info("Bot profil rasmi (logo) o'rnatildi.")
            except Exception as e:
                log.warning(
                    "Profil rasmini o'rnatib bo'lmadi (fayl yoki Telegram talablari): %s",
                    e,
                )
        else:
            log.warning("Logo fayli topilmadi: %s", logo_path)

    log.info("Bot ishga tushmoqda (aiogram)...")
    await dp.start_polling(bot, on_startup=on_startup)


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("BOT_TOKEN .env faylida yo'q.", file=sys.stderr)
        sys.exit(1)
    import asyncio

    asyncio.run(main())
