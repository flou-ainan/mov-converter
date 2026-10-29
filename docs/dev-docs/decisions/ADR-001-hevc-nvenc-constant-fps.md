# ADR 001 — HEVC via NVENC with CPU fallback, constant framerate, verify-before-delete

**Status:** accepted
**Date:** 2026-10-28

## Context

The owner records course videos on an iPhone. The files are `.MOV` with three problems for the production pipeline:

1. **Variable framerate** — iPhones record VFR; editors and platforms behave unpredictably with it.
2. **Codec** — HEVC/H.265 carries HDR and 10 bits, but raw iPhone MOV containers are heavy and awkward to handle downstream.
3. **Safety** — the originals are the only copy of the footage; a converter that loses or corrupts one is worse than no converter.

The machine has an NVIDIA RTX 2070 Super with NVENC, and `ffmpeg` is already installed.

## Decision

- Output container **`.mp4`**, video codec **HEVC (H.265)** with the `hvc1` tag (Apple/QuickTime compatibility), audio kept as AAC (copied losslessly when already AAC).
- **GPU first:** NVENC `p7`/`tune=hq` VBR with constant quality (`-cq 19`), `spatial-aq` + `temporal-aq`, lookahead 32. CUDA decode (`-hwaccel cuda`) is used when the build reports it.
- **Automatic fallback chain:** GPU+CUDA decode → GPU-only → CPU (`libx265`, CRF 18, preset medium). Each failed attempt is logged with the exact command before moving to the next mode.
- **Framerate forced to constant:** the average fps is snapped to the nearest standard value (23.976/29.97/59.94 as exact `x/1001` fractions), applied via `-vf fps=…` + `-r`.
- **10-bit/HDR preserved:** `main10`/`p010le` when the source is 10/12-bit; colour primaries, transfer and space carried to the output. Audio at 256k AAC only when re-encoding is unavoidable.
- **Verify before delete:** every converted file must open, contain video, match the original duration (±1 s), and decode 2 s from both start and end with no stderr. Only verified files are offered for deletion (never automatic without `-s`).
- `+faststart` so the MP4 is streamable, `-map_metadata 0` to keep metadata.

## Alternatives considered

- **H.264 (libx264 / h264_nvenc):** universal compatibility, but loses 10-bit/HDR and produces much larger files at the same quality. Revisit only if a consumer platform chokes on HEVC (see roadmap idea).
- **AV1:** better compression but slow to encode and weaker tooling support for the owner's pipeline; not worth it yet.
- **Copy stream without re-encode (`-c copy`):** keeps VFR — the main problem to solve. Not viable.
- **CPU-only (libx265):** highest quality per bit, but ~10–20× slower than NVENC on long course videos. Kept only as the fallback path.

## Consequences

- Output requires HEVC playback support (fine for the owner's editor and for YouTube/Hotmart uploads; verify before publishing elsewhere).
- NVENC quality at `-cq 19` is visually lossless at normal viewing, slightly weaker than libx265 CRF 18 in hard scenes — accepted trade for the speed.
- The fallback chain means a broken driver or FFmpeg build degrades speed silently instead of failing; the error log records which mode actually ran.
- Verification doubles the read of each converted file (cheap ffprobe + 4 s of decode), accepted as the price of never deleting an original that points to a broken MP4.
