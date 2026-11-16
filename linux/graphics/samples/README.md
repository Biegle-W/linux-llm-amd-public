# Generated image and video samples

Every image and video the ComfyUI server on the dual RX 7900 XTX machine has written to its output folder, kept at the
same relative paths. Owner rule (November 16, 2026): all image and video generation samples are added to the repository.

- `media-manifest.json` lists each file with its generation date, size, dimensions and SHA-256 (of the original and of the copy here).
- `contact-sheet.jpg` shows a thumbnail of every file, in manifest order (first frame for videos).
- PNG pixels and the encoded MP4 video and audio streams are unchanged. The embedded generation and workflow metadata was removed.
- Refresh after new generations with `python3 graphics/export-samples.py`; it copies only files that are not here yet.

These are test outputs of fixed validation prompts (a teapot, a lighthouse, toast). They include failed and superseded runs:
for example the two sunset clips are the wrong output that the Triton flag produced on November 7, kept as evidence.
The MiniMax H3 Image samples of November 15 are described in [the report](../MINIMAX-H3-IMAGE-2026-11-15.md).
