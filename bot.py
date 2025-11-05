#!/usr/bin/env python3
\"\"\"Simple Telegram bot to download .m3u8 streams and send MP4 back.
Works on Railway. Prefers N_m3u8DL-RE if USE_N=1 and binary exists, otherwise uses ffmpeg copy.
\"\"\"
import os
import asyncio
import logging
import tempfile
import shutil
from urllib.parse import urlparse
from pathlib import Path
import subprocess

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

BOT_TOKEN = os.getenv(\"BOT_TOKEN\")
if not BOT_TOKEN:
    raise RuntimeError(\"Set BOT_TOKEN environment variable in Railway settings\")


USE_N = os.getenv(\"USE_N\", \"0\") == \"1\"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


def safe_filename_from_url(url: str):
    parsed = urlparse(url)
    name = os.path.basename(parsed.path) or \"output\"
    name = \"\".join(c for c in name if c.isalnum() or c in \"._-\") or \"output\"
    if not name.lower().endswith(\".mp4\"):
        name += \".mp4\"
    return name


async def run_subprocess(cmd, cwd=None, timeout=None):
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, b\"\", b\"timeout\"\n    return proc.returncode, stdout, stderr\n\n\n@dp.message_handler(commands=[\"start\"])\nasync def cmd_start(message: types.Message):\n    await message.reply(\"مرحبًا! أرسل رابط .m3u8 أو استخدم /download <الرابط> وسأقوم بتحميله وتحويله.\")\n\n\n@dp.message_handler(commands=[\"download\"])\nasync def cmd_download(message: types.Message):\n    args = message.get_args().strip()\n    if not args:\n        await message.reply(\"أرسل: /download <رابط_m3u8>\")\n        return\n    await handle_m3u8_url(message, args)\n\n\n@dp.message_handler()\nasync def text_message(message: types.Message):\n    text = (message.text or \"\").strip()\n    if text.lower().endswith('.m3u8') or '.m3u8' in text:\n        for tok in text.split():\n            if tok.startswith('http') and '.m3u8' in tok:\n                await handle_m3u8_url(message, tok)\n                return\n    # ignore other messages\n\n\nasync def handle_m3u8_url(message: types.Message, url: str):\n    chat_id = message.chat.id\n    status = await message.reply(f\"أتحقق من الرابط وأبدأ التحميل: {url}\")\n\n    tmpdir = Path(tempfile.mkdtemp(prefix=\"m3u8dl_\"))\n    out_name = safe_filename_from_url(url)\n    out_path = tmpdir / out_name\n\n    try:\n        # try N_m3u8DL-RE\n        n_path = shutil.which('N_m3u8DL-RE') or (Path.cwd() / 'N_m3u8DL-RE')\n        used_n = False\n        if USE_N and Path(n_path).exists():\n            await status.edit_text(\"جاري التنزيل باستخدام N_m3u8DL-RE — هذا أفضل للحالات المشفرة والـ DRM-less segments\")\n            cmd = [str(n_path), url, '--save-name', out_name.rsplit('.',1)[0], '--save-dir', str(tmpdir), '--no-log']\n            rc, out, err = await run_subprocess(cmd, timeout=600)\n            if rc == 0:\n                used_n = True\n            else:\n                await status.edit_text(f\"N_m3u8DL-RE فشل، سأنفّذ ffmpeg كبديل.\\nرسالة خطأ موجزة: {err[:400]}\")\n\n        if not used_n:\n            await status.edit_text(\"جاري التحويل بواسطة ffmpeg (نسخ التدفقات) — إن لم تنجح هذه الطريقة قد تحتاج N_m3u8DL-RE.\")\n            ffmpeg_cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', url, '-c', 'copy', str(out_path)]\n            rc, out, err = await run_subprocess(ffmpeg_cmd, timeout=900)\n            if rc != 0 or not out_path.exists():\n                await status.edit_text(f\"فشل ffmpeg أثناء التحويل.\\nموجز الخطأ:\\n{err.decode(errors='ignore')[:800]}\")\n                return\n\n        if used_n:\n            # find produced file\n            candidates = list(tmpdir.glob('**/*'))\n            mp = None\n            for c in candidates:\n                if c.is_file() and c.suffix.lower() in ['.mp4', '.mkv', '.ts', '.mov', '.mp3', '.m4a']:\n                    mp = c\n                    break\n            if mp is None:\n                await status.edit_text('انتهت عملية N ولكن لم يتم العثور على ملف مخرجات.')\n                return\n            out_path = mp\n\n        size_mb = out_path.stat().st_size / (1024*1024)\n        await status.edit_text(f\"الملف جاهز. الحجم: {size_mb:.1f} MB — جارٍ الإرسال إلى Telegram...\")\n\n        try:\n            with out_path.open('rb') as f:\n                await bot.send_document(chat_id, (out_path.name, f))\n            await status.delete()\n        except Exception as e:\n            await status.edit_text(f\"الملف تم إنشاؤه لكن لم يُرسَل إلى Telegram: {e}\\nإذا كان الملف كبيرًا، فكّر برفعه لسحابة ومشاركة الرابط.\")\n\n    finally:\n        # cleanup\n        try:\n            for p in tmpdir.glob('*'):\n                if p.is_file():\n                    p.unlink()\n            tmpdir.rmdir()\n        except Exception:\n            pass\n\n\nif __name__ == '__main__':\n    executor.start_polling(dp, skip_updates=True)\n