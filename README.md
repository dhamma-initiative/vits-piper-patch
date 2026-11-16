# vits-piper-patch

Independent phoneme override endpoint for SuttaPlayer and the Piper voice.

A single pronunciation fix must not require a `suttas` release (text, dictionary,
vector index) or a `vits-piper` release (model, voice config). This repository
is served by GitHub Pages on its own cadence, so a patch is one small JSON
commit.

Endpoint:

```
https://dhamma-initiative.github.io/vits-piper-patch/phoneme-patches.json
```

## Contract

`main` always holds the **current** patch file. When there are no overrides the
language maps are empty objects; the file is never deleted, so the URL is always
resolvable. `patchVersion` is monotonic and is what the app logs and reports.

```json
{
  "schemaVersion": 1,
  "patchVersion": "2026-11-17-01",
  "base": { "suttas": "261115", "vits": "ver2-281109-projected2" },
  "english": { "penchant": "pˈɛnt‍ʃˈant" },
  "pali": {},
  "notes": ["free-form; shown in diagnostics"]
}
```

- Keys are lower-case words; values are IPA for the voice.
- Zero-width characters are rejected by CI: copy/paste from a spreadsheet can
  embed U+200B–U+200D or U+FEFF, which the phonemizer drops and which make the
  published value differ from the spoken one.
- `base` is a guard. The app skips a patch whose base does not match the
  endpoints it loaded, and says so in Diagnostics and in the console.
- Entries here win over the canonical dictionary and over the voice
  `customPhonemes`.

## Lightweight verification first

Do not publish to test a candidate. Use the scratch loop described in
`dt.o-orchestration/docs/runbooks/PHONEME-TRIAGE.md`:

```bash
cd ~/dev/di-oc/dt.o-orchestration
python3 scripts/try-phoneme.py penchant "pˈɛntʃˈɛnt"
# open <dev-url>/?patch=/scratch/phoneme-patches.json&verbose=1#diagnostics
```

That writes a gitignored file, applies the same merge path as production, and
needs no commit, version bump or release. Publish here only after the candidate
is accepted in context.

## Workflow

1. Add the defect to
   `dt.o-orchestration/sponsor-notes/phoneme-overrides-defects.csv`
   (`word|desired_ipa|source|line`).
2. Regenerate and publish:

   ```bash
   cd ~/dev/di-oc/dt.o-orchestration
   python3 scripts/make-phoneme-patches.py \
     --csv sponsor-notes/phoneme-overrides-defects.csv \
     --out ~/dev/di-oc/vits-piper-patch/phoneme-patches.json \
     --suttas 261115 --vits ver2-281109-projected2 --lang en \
     --version 2026-11-17-02
   cd ~/dev/di-oc/vits-piper-patch
   git add phoneme-patches.json && git commit -m "patch: <word>" && git push
   ```

3. In the app: Help & Docs → Diagnostics, confirm
   `patch.status: ok` and `patch.appliedVersion` matches.

GitHub Pages caches for up to 10 minutes (`cache-control: max-age=600`). The app
fetches with `cache: "no-cache"`, so it revalidates via ETag; if a change appears
stale, bump `patchVersion` and reload.

## Promotion (keeps this file small)

The patch is temporary by design. At the next release:

- general English/Pali fixes → `build.src/phoneme/phoneme-overrides-en.json` in
  the suttas build (rebuilds the dictionary);
- voice-specific renderings → `customPhonemes` in the vits phonemizer config.

Then empty `english` and `pali`, bump `patchVersion`, and commit. The base guard
also forces a review whenever a new suttas or vits release lands.

See `dt.o-orchestration/decisions/ADR-0020-phoneme-override-lifecycle.md`.

## Notes

- No build step, no assets, no service worker: the app fetches this file with
  `cache: "no-cache"` and treats failure as non-fatal (dictionary wins).
- GitHub Pages sends `access-control-allow-origin: *`, so the cross-origin fetch
  from the app works without additional configuration.
- The app endpoint is set by `endpoints.phonemePatchesUrl` in
  `sutta-player/suttaplayer.config.json`; local development keeps the relative
  `./phoneme-patches.json`.
