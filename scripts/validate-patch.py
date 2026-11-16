#!/usr/bin/env python3
"""Validate phoneme-patches.json before it is published.

Guards against the failure modes that silently disable a patch:
malformed JSON, unsupported schema, missing base, and keys that are not
lower-case (the phonemizer looks up lower-case words).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SUTTAS_VERSION = re.compile(r"^\d{6}$|^\d{4}\.\d{2}\.\d{2}$")
IPA_OK = re.compile(r"^[^\s]+$")


def fail(message: str) -> int:
    print(f"INVALID: {message}")
    return 1


def main(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return fail(f"{path} is not valid JSON: {err}")

    if data.get("schemaVersion") != 1:
        return fail("schemaVersion must be 1")
    if not isinstance(data.get("patchVersion"), str) or not data["patchVersion"].strip():
        return fail("patchVersion is required")

    base = data.get("base")
    if not isinstance(base, dict) or not base.get("suttas") or not base.get("vits"):
        return fail("base.suttas and base.vits are required (the app skips mismatches)")
    if not SUTTAS_VERSION.match(str(base["suttas"])):
        return fail(f"base.suttas looks wrong: {base['suttas']}")

    total = 0
    for language in ("english", "pali"):
        entries = data.get(language, {})
        if not isinstance(entries, dict):
            return fail(f"{language} must be an object")
        for word, ipa in entries.items():
            total += 1
            if word != word.lower():
                return fail(f"{language} key must be lower-case: {word}")
            if not isinstance(ipa, str) or not ipa.strip():
                return fail(f"{language}.{word} has no IPA")
            if not IPA_OK.match(ipa):
                return fail(f"{language}.{word} IPA contains whitespace (words are synthesised as one token)")

    print(f"ok: {path.name} {data['patchVersion']} base {base['suttas']}/{base['vits']} ({total} entries)")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "phoneme-patches.json")
    raise SystemExit(main(target))
