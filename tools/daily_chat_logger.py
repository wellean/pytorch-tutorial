from __future__ import annotations

import argparse
import hashlib
from datetime import date, datetime
from pathlib import Path
import re
from typing import List, Tuple


def build_note_path(base_dir: Path, note_date: date) -> Path:
    return base_dir / "notes" / f"note_{note_date:%Y_%m_%d}.md"


def ensure_note_file(note_path: Path) -> None:
    if note_path.exists():
        return
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(f"# {note_path.stem}\n\n", encoding="utf-8")


def prompt_multiline(title: str) -> str:
    print(f"{title}（输入 END 单独一行结束）")
    lines: list[str] = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def append_entry(note_path: Path, question: str, answer: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    block = (
        f"## {now}\n\n"
        f"User:\n{question}\n\n"
        f"GitHub Copilot:\n{answer}\n\n"
        "---\n\n"
    )
    with note_path.open("a", encoding="utf-8") as f:
        f.write(block)


def append_entries(note_path: Path, entries: List[Tuple[str, str]]) -> None:
    with note_path.open("a", encoding="utf-8") as f:
        for question, answer in entries:
            now = datetime.now().strftime("%H:%M:%S")
            block = (
                f"## {now}\n\n"
                f"User:\n{question}\n\n"
                f"GitHub Copilot:\n{answer}\n\n"
                "---\n\n"
            )
            f.write(block)


def append_raw_transcript(note_path: Path, transcript: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    block = (
        f"## {now}\n\n"
        "Raw Chat Transcript:\n\n"
        f"{transcript.strip()}\n\n"
        "---\n\n"
    )
    with note_path.open("a", encoding="utf-8") as f:
        f.write(block)


def compute_content_hash(content: str) -> str:
    """Compute a short hash of content for deduplication."""
    return hashlib.md5(content.strip().encode()).hexdigest()[:8]


def content_exists_in_file(note_path: Path, content_hash: str) -> bool:
    """Check if a content hash already exists in the note file."""
    if not note_path.exists():
        return False
    file_content = note_path.read_text(encoding="utf-8")
    return f"Hash: {content_hash}" in file_content


def append_raw_transcript_with_dedup(
    note_path: Path, transcript: str, force: bool = False
) -> bool:
    """Append raw transcript with deduplication check."""
    content_hash = compute_content_hash(transcript)

    if not force and content_exists_in_file(note_path, content_hash):
        return False

    now = datetime.now().strftime("%H:%M:%S")
    block = (
        f"## {now}\n\n"
        "Raw Chat Transcript:\n\n"
        f"{transcript.strip()}\n\n"
        f"Hash: {content_hash}\n\n"
        "---\n\n"
    )
    with note_path.open("a", encoding="utf-8") as f:
        f.write(block)
    return True


def read_clipboard_text() -> str:
    import os
    if not os.environ.get("DISPLAY"):
        raise SystemExit("服务器无桌面环境（找不到 $DISPLAY 变量），无法直接读取剪贴板。\n建议方案：\n1. 在当前目录下新建一个 chat_temp.txt\n2. 将本地内容粘贴进 chat_temp.txt 中\n3. 运行含 --from-file 参数的自动记录 Task，或手动执行：python tools/daily_chat_logger.py --from-file chat_temp.txt --fallback-raw")
    try:
        import tkinter as tk
    except Exception as exc:
        raise SystemExit(f"读取剪贴板失败：{exc}") from exc

    root = tk.Tk()
    root.withdraw()
    try:
        text = root.clipboard_get()
    except Exception as exc:
        raise SystemExit(f"读取剪贴板失败：{exc}") from exc
    finally:
        root.destroy()
    return text


def parse_chat_pairs(text: str) -> List[Tuple[str, str]]:
    """Parse common copied chat formats into (user, assistant) pairs."""
    user_tag = r"(?:User|You|你|我)"
    assistant_tag = r"(?:GitHub\s*Copilot|Copilot|Assistant|助手)"
    pattern = re.compile(
        rf"(?:^|\n)\s*{user_tag}:\s*(.*?)\s*(?:^|\n)\s*{assistant_tag}:\s*(.*?)(?=(?:\n\s*{user_tag}:)|\Z)",
        re.S | re.I,
    )
    pairs: List[Tuple[str, str]] = []
    for match in pattern.finditer(text):
        q = match.group(1).strip()
        a = match.group(2).strip()
        if q and a:
            pairs.append((q, a))
    return pairs


def parse_date(date_text: str | None) -> date:
    if not date_text:
        return date.today()
    return datetime.strptime(date_text, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="把每日提问和回答自动追加到 note_YYYY_MM_DD.md"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="工作区根目录路径（默认：脚本上一级目录）",
    )
    parser.add_argument("--date", help="指定日期，格式 YYYY-MM-DD")
    parser.add_argument("--question", "-q", help="提问内容")
    parser.add_argument("--answer", "-a", help="回答内容")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互式输入提问和回答（支持多行）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览输出文件和内容，不写入",
    )
    parser.add_argument(
        "--from-clipboard",
        action="store_true",
        help="从剪贴板读取整段聊天并批量导入",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        help="从文本文件读取整段聊天并批量导入（调试/回放用）",
    )
    parser.add_argument(
        "--fallback-raw",
        action="store_true",
        help="当无法识别问答对时，直接按原文记录整段聊天",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制写入，即使内容已存在（覆盖去重检查）",
    )

    args = parser.parse_args()

    note_date = parse_date(args.date)
    workspace = args.workspace.resolve()
    note_path = build_note_path(workspace, note_date)

    if args.from_clipboard or args.from_file:
        if args.from_clipboard:
            raw_text = read_clipboard_text()
        else:
            raw_text = args.from_file.read_text(encoding="utf-8")

        entries = parse_chat_pairs(raw_text)
        if not entries and not args.fallback_raw:
            raise SystemExit(
                "未识别到可导入的聊天内容，请确认文本里包含发言人标签，或加 --fallback-raw。"
            )

        if args.dry_run:
            print(f"[Dry Run] 目标文件: {note_path}")
            if entries:
                print(f"识别到 {len(entries)} 组问答。")
            else:
                print("未识别到标准问答对，将按原文记录。")
            print("\n---\n")
            if entries:
                first_q, first_a = entries[0]
                print(f"第一组 User:\n{first_q}\n")
                print(f"第一组 GitHub Copilot:\n{first_a}\n")
            else:
                print(raw_text[:1000])
            return

        ensure_note_file(note_path)
        if entries:
            append_entries(note_path, entries)
            print(f"批量记录成功: {note_path}，共导入 {len(entries)} 组问答")
        else:
            if append_raw_transcript_with_dedup(note_path, raw_text, args.force):
                print(f"原文记录成功: {note_path}，共导入 1 段聊天原文")
            else:
                print(f"提示: 内容已存在，跳过写入。使用 --force 强制写入。")
        return

    if args.interactive or not (args.question and args.answer):
        question = prompt_multiline("请输入 User 提问")
        answer = prompt_multiline("请输入 GitHub Copilot 回答")
    else:
        question = args.question.strip()
        answer = args.answer.strip()

    if not question:
        raise SystemExit("提问内容为空，已取消写入。")
    if not answer:
        raise SystemExit("回答内容为空，已取消写入。")

    if args.dry_run:
        print(f"[Dry Run] 目标文件: {note_path}")
        print("\n---\n")
        print(f"User:\n{question}\n")
        print(f"GitHub Copilot:\n{answer}\n")
        return

    ensure_note_file(note_path)
    append_entry(note_path, question, answer)
    print(f"记录成功: {note_path}")


if __name__ == "__main__":
    main()
