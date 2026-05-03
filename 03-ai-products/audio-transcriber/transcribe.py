"""
Локальная транскрибация через faster-whisper.
Модель скачивается при первом запуске в кэш Hugging Face (~/.cache/huggingface).
Нужен ffmpeg в PATH для mp3/m4a и др. (https://ffmpeg.org/download.html)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Кэш Hugging Face на Windows без симлинков — тише предупреждение hub о symlinks.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def list_folder_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    out = [p for p in folder.iterdir() if p.is_file()]
    return sorted(out, key=lambda x: x.name.lower())


def pick_file_interactive(wav_dir: Path) -> Path | None:
    wav_dir = wav_dir.resolve()
    files = list_folder_files(wav_dir)
    if not files:
        print(f"В папке нет файлов: {wav_dir}", file=sys.stderr)
        return None
    print(f"Папка: {wav_dir}")
    for i, p in enumerate(files, start=1):
        print(f"  {i}. {p.name}")
    try:
        raw = input("Номер файла: ").strip()
    except EOFError:
        print("Нет интерактивного ввода — укажите путь к файлу аргументом.", file=sys.stderr)
        return None
    if not raw.isdigit():
        print("Введите целый номер из списка.", file=sys.stderr)
        return None
    idx = int(raw)
    if idx < 1 or idx > len(files):
        print("Номер вне диапазона.", file=sys.stderr)
        return None
    return files[idx - 1].resolve()


def transcribe_file(path: Path, args: argparse.Namespace) -> int:
    try:
        from faster_whisper import WhisperModel  # pyright: ignore[reportMissingImports]
    except ImportError:
        print("Установите зависимости: pip install -r requirements.txt", file=sys.stderr)
        return 1

    device = args.device
    if device == "auto":
        try:
            import ctranslate2  # pyright: ignore[reportMissingImports]

            has_cuda = ctranslate2.get_cuda_device_count() > 0
        except Exception:
            has_cuda = False
        device = "cuda" if has_cuda else "cpu"
        compute_type = args.compute_type or ("float16" if has_cuda else "int8")
    else:
        compute_type = args.compute_type or (
            "float16" if device == "cuda" else "int8"
        )

    print(f"Загрузка модели {args.model} ({device}, {compute_type})…", flush=True)
    model = WhisperModel(args.model, device=device, compute_type=compute_type)

    lang = args.language
    segments, info = model.transcribe(
        str(path),
        language=lang,
        vad_filter=True,
    )
    if lang is None:
        print(f"Язык: {info.language} (уверенность {info.language_probability:.2f})", flush=True)

    lines: list[str] = []
    for seg in segments:
        line = seg.text.strip()
        if line:
            lines.append(line)

    text = "\n".join(lines) if lines else ""
    out = args.output
    if out is None:
        out = path.with_suffix(".txt")
    else:
        out = out.resolve()
    out.write_text(text, encoding="utf-8")
    print(f"Готово: {out} ({len(text)} символов)", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Транскрибация аудио/видео локально")
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=None,
        help="Путь к файлу. Если не указан — нумерованный выбор среди всех файлов в папке wav",
    )
    parser.add_argument(
        "--wav-dir",
        type=Path,
        default=Path("wav"),
        help="Папка для интерактивного выбора: в списке все файлы (по умолчанию ./wav)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="small",
        choices=[
            "tiny",
            "tiny.en",
            "base",
            "base.en",
            "small",
            "small.en",
            "medium",
            "medium.en",
            "large-v2",
            "large-v3",
            "distil-large-v3",
        ],
        help="Размер модели: tiny — быстро/хуже, large-v3 — медленно/лучше (по умолчанию small)",
    )
    parser.add_argument(
        "-l",
        "--language",
        default=None,
        help="Код языка (ru, en, …). Если не указан — автоопределение",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Файл для текста (.txt). По умолчанию: рядом с входом, расширение .txt",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Устройство: auto (CUDA если есть), cpu, cuda",
    )
    parser.add_argument(
        "--compute-type",
        default=None,
        help="Переопределить тип вычислений (float16, int8, int8_float16, float32). "
        "По умолчанию подбирается под device.",
    )
    args = parser.parse_args()

    if args.input is None:
        path = pick_file_interactive(args.wav_dir)
        if path is None:
            return 1
    else:
        path = args.input.resolve()
        if not path.is_file():
            print(f"Файл не найден: {path}", file=sys.stderr)
            return 1

    return transcribe_file(path, args)


if __name__ == "__main__":
    raise SystemExit(main())
