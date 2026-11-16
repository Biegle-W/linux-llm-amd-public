"""Copy every generated image/video sample into graphics/samples with embedded workflow metadata removed.
PNG pixels and the encoded MP4 streams are unchanged. Writes graphics/samples/media-manifest.json and a contact sheet."""
import datetime, hashlib, json, subprocess, sys
from pathlib import Path
from PIL import Image
ROOT = Path.home() / "Desktop/local-llm"
SRC, DST = ROOT / "graphics/outputs", ROOT / "graphics/samples"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows, thumbs = [], []
for src in sorted(p for p in SRC.rglob("*") if p.is_file()):
    rel = src.relative_to(SRC); out = DST / rel; out.parent.mkdir(parents=True, exist_ok=True)
    row = {"file": str(rel), "generated": datetime.date.fromtimestamp(src.stat().st_mtime).isoformat(), "source_sha256": sha(src)}
    if src.suffix.lower() == ".png":
        im = Image.open(src); im.load(); clean = Image.new(im.mode, im.size); clean.putdata(list(im.getdata()))
        if not out.exists(): clean.save(out, "PNG")
        chk = Image.open(out); chk.load()
        assert chk.tobytes() == im.tobytes() and not chk.info, rel
        row.update(kind="image", width=im.width, height=im.height, pixels_unchanged=True)
        t = im.convert("RGB"); t.thumbnail((256, 256)); thumbs.append((str(rel), t))
    elif src.suffix.lower() == ".mp4":
        if not out.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map", "0", "-c", "copy", "-map_metadata", "-1", "-fflags", "+bitexact", str(out)], check=True)
        pr = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=codec_name,width,height,nb_read_frames:format_tags", "-of", "json", str(out)]))
        v = next(s for s in pr["streams"] if s.get("width"))
        tags = {k: v2 for k, v2 in pr.get("format", {}).get("tags", {}).items() if k not in ("major_brand", "minor_version", "compatible_brands", "encoder")}
        assert not tags, (rel, tags)
        row.update(kind="video", width=v["width"], height=v["height"], frames=int(v["nb_read_frames"]), streams=[s["codec_name"] for s in pr["streams"]], streams_copied=True)
        fr = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"])
        import io; t = Image.open(io.BytesIO(fr)).convert("RGB"); t.thumbnail((256, 256)); thumbs.append((str(rel), t))
    else:
        print("skipped", rel); continue
    row.update(bytes=out.stat().st_size, sha256=sha(out)); rows.append(row)
(DST / "media-manifest.json").write_text(json.dumps({"method": "Every file from the ComfyUI output folder; PNG pixels and encoded MP4 video/audio unchanged; embedded generation/workflow metadata removed", "count": len(rows), "artifacts": rows}, indent=1) + "\n")
cols = 9; r = (len(thumbs) + cols - 1) // cols; sheet = Image.new("RGB", (cols * 260, r * 260), "white")
for i, (_, t) in enumerate(thumbs): sheet.paste(t, ((i % cols) * 260 + 2, (i // cols) * 260 + 2))
sheet.save(DST / "contact-sheet.jpg", quality=80)
print(len(rows), "files", sum(x["bytes"] for x in rows) // 1048576, "MB"); print("\n".join(f"{i:2d} {n}" for i, (n, _) in enumerate(thumbs)))
