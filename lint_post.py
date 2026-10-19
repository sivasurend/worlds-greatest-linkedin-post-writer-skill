#!/usr/bin/env python3
"""Lint a LinkedIn post draft against the linkedin-bookmark-writer bans.

Usage:
    python lint_post.py post.txt
    python lint_post.py post.txt --allow-hashtags --allow-emojis
    cat post.txt | python lint_post.py -

Exit code 0 when clean, 1 when any error is found. Warnings never fail.
"""

import argparse
import re
import sys

BANNED_PHRASES = [
    "in today's world",
    "in today's fast-paced world",
    "game changer",
    "game-changer",
    "game changing",
    "game-changing",
    "the future belongs to",
    "let that sink in",
    "read that again",
    "we are still early",
    "we're still early",
    "unlocking potential",
    "unlock potential",
    "at the end of the day",
    "here's your linkedin post",
    "here is your linkedin post",
]

BAIT_ENDINGS = [
    r"thoughts\??",
    r"agree\??",
    r"what do you think\??",
    r"comment below\.?",
    r"like if you agree\.?",
    r"let me know in the comments\.?",
    r"drop a comment\.?",
]

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF]"
)


def lint(text, allow_hashtags=False, allow_emojis=False):
    errors, warnings = [], []
    lines = text.splitlines()
    normalized = text.replace("’", "'").lower()

    for i, line in enumerate(lines, 1):
        if "\u2014" in line:
            errors.append(f"line {i}: em dash found")
        if "\u2013" in line:
            errors.append(f"line {i}: en dash found")
        if re.search(r"\s--\s|\s-\s", line):
            errors.append(f"line {i}: spaced hyphen used as a dash")
        if re.search(r"\bhonest(ly)?\b", line, re.IGNORECASE):
            errors.append(f"line {i}: 'honest' or 'honestly'")
        if re.search(r"\*\*|__|^\s*#{1,6}\s|`", line):
            errors.append(f"line {i}: markdown formatting")
        if re.match(r"^\s*[*-]\s+", line):
            errors.append(f"line {i}: markdown bullet; use the bullet character instead")
        if not allow_hashtags and re.search(r"(^|\s)#[A-Za-z]\w*", line):
            errors.append(f"line {i}: hashtag")
        if not allow_emojis and EMOJI_RE.search(line):
            errors.append(f"line {i}: emoji")

    for phrase in BANNED_PHRASES:
        if phrase in normalized:
            errors.append(f"banned phrase: '{phrase}'")

    non_empty = [l.strip() for l in lines if l.strip()]
    if non_empty:
        last = non_empty[-1].lower().replace("’", "'")
        for pattern in BAIT_ENDINGS:
            if re.fullmatch(pattern, last):
                errors.append(f"engagement bait ending: '{non_empty[-1]}'")
        if len(non_empty[0]) > 150:
            warnings.append(
                f"opening line is {len(non_empty[0])} characters; a long hook may be cut off before 'see more'"
            )
        first = non_empty[0].lower()
        if first.startswith(("i've been thinking", "i have been thinking", "let's talk about", "in this post")):
            warnings.append("opening line is a warm-up; lead with the claim, number, or problem")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="post file, or - for stdin")
    parser.add_argument("--allow-hashtags", action="store_true")
    parser.add_argument("--allow-emojis", action="store_true")
    args = parser.parse_args()

    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    errors, warnings = lint(text, args.allow_hashtags, args.allow_emojis)

    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARN    {w}")
    if not errors and not warnings:
        print("Clean: no bans found.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
