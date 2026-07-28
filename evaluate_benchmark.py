#!/usr/bin/env python3
"""evaluate_benchmark.py — Non-destructive evaluation of OmniVision pipeline.

Usage:
    python evaluate_benchmark.py [--model blip] [--skip-translation] [--max-images N]

Output:
    evaluation/evaluation_report.json
    evaluation/evaluation_summary.md
    evaluation/benchmark_results.csv
"""

import argparse, csv, json, os, sys, time
from collections import defaultdict
from pathlib import Path

os.environ["PROFILE"] = "development"
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import torch
from backend.app.managers.model_manager import get_model_manager
from backend.app.services.caption_service import CaptionService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.grounding_service import GroundingService
from backend.app.services.translation_service import TranslationService
from backend.app.config.settings import get_settings
from backend.app.exceptions.handlers import TranslationException, CriticalAIException

settings = get_settings()
PROJECT_ROOT = Path(__file__).parent
TEST_IMAGES_DIR = PROJECT_ROOT / "test_images"
OUTPUT_DIR = PROJECT_ROOT / "evaluation"
GROUND_TRUTH_PATH = TEST_IMAGES_DIR / "ground_truth.json"


def load_image(path):
    img = Image.open(path).convert("RGB")
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    return img


def clip_similarity(mm, image, text):
    bundle = mm.get_model("clip")
    proc, model = bundle["processor"], bundle["model"]
    dev = mm.device
    with torch.no_grad():
        ii = proc(images=image, return_tensors="pt").to(dev)
        imf = model.get_image_features(**ii)
        imf = imf / imf.norm(p=2, dim=-1, keepdim=True)
        ti = proc(text=[text], return_tensors="pt", padding=True).to(dev)
        tf = model.get_text_features(**ti)
        tf = tf / tf.norm(p=2, dim=-1, keepdim=True)
        return (imf @ tf.T).item()


def classify_failure(e):
    if e.get("stage_error"):
        return "stage_error"
    wc = e.get("caption_word_count", 0)
    if 0 < wc < 3:
        return "truncated_caption"
    if e.get("unique_word_ratio", 1) < 0.5:
        return "repeated_tokens"
    if e.get("confidence_label") in ("Reject", None):
        if e.get("top_score", 1) < 0.3:
            return "retrieval_mismatch"
        return "low_confidence"
    return None


def collect_images():
    imgs = []
    if TEST_IMAGES_DIR.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            imgs.extend(TEST_IMAGES_DIR.rglob(ext))
    rt = PROJECT_ROOT / "test_image.jpg"
    if rt.exists():
        imgs.append(rt)
    imgs = sorted(set(imgs))
    result = []
    for img in imgs:
        p = img.parent
        cat = "root" if p.name == "test_images" else p.name
        result.append({"path": str(img), "category": cat, "filename": img.name})
    return result


def eval_image(mm, services, info, gt, skip_tx):
    cs, es, rs, gs, ts = services
    path, cat, fn = info["path"], info["category"], info["filename"]
    rel = os.path.relpath(path, str(TEST_IMAGES_DIR))
    entry = {
        "filename": fn, "path": path, "category": cat, "caption": None,
        "caption_latency_ms": 0, "caption_word_count": 0, "unique_word_ratio": 1,
        "clip_score": 0, "ground_truth": gt.get(rel, ""), "gt_score": None,
        "embedding_latency_ms": 0, "retrieval_results": [], "retrieval_latency_ms": 0,
        "top_score": 0, "top_entity": None, "confidence_label": None, "reason": None,
        "grounding_latency_ms": 0, "translations": {}, "translation_latency_ms": 0,
        "total_latency_ms": 0, "stage_error": False, "failure_type": None,
    }
    try:
        image = load_image(path)
    except Exception as e:
        entry["stage_error"] = True
        entry["reason"] = f"Load fail: {e}"
        entry["failure_type"] = "stage_error"
        return entry

    t0 = time.time()
    try:
        caption = cs.generate(image, detailed=True)
    except CriticalAIException as e:
        entry["stage_error"] = True
        entry["reason"] = f"Caption fail: {e}"
        entry["failure_type"] = "stage_error"
        return entry
    entry["caption"] = caption
    entry["caption_latency_ms"] = round((time.time() - t0) * 1000, 2)
    words = caption.split()
    entry["caption_word_count"] = len(words)
    entry["unique_word_ratio"] = round(
        len(set(w.lower() for w in words)) / max(len(words), 1), 4
    )

    try:
        entry["clip_score"] = round(clip_similarity(mm, image, caption), 4)
    except Exception:
        entry["clip_score"] = 0

    gt2 = entry["ground_truth"]
    if gt2:
        try:
            entry["gt_score"] = round(clip_similarity(mm, image, gt2), 4)
        except Exception:
            pass

    t0 = time.time()
    try:
        embedding = es.generate_embedding(image)
    except CriticalAIException as e:
        entry["stage_error"] = True
        entry["reason"] = f"Embed fail: {e}"
        entry["failure_type"] = "stage_error"
        return entry
    entry["embedding_latency_ms"] = round((time.time() - t0) * 1000, 2)

    t0 = time.time()
    try:
        retrieved = rs.search(embedding, k=3)
    except Exception:
        retrieved = []
    entry["retrieval_latency_ms"] = round((time.time() - t0) * 1000, 2)
    entry["retrieval_results"] = retrieved
    if retrieved:
        entry["top_score"] = round(retrieved[0].get("score", 0), 4)
        entry["top_entity"] = retrieved[0].get("entity")

    t0 = time.time()
    try:
        gr = gs.evaluate_and_ground(caption, retrieved)
    except Exception as e:
        entry["stage_error"] = True
        entry["reason"] = f"Ground fail: {e}"
        entry["failure_type"] = "stage_error"
        return entry
    entry["grounding_latency_ms"] = round((time.time() - t0) * 1000, 2)
    entry["confidence_label"] = gr.get("confidenceLabel")
    entry["reason"] = gr.get("reason")
    entry["top_score"] = gr.get("top_score", entry["top_score"])
    entry["top_entity"] = gr.get("top_entity", entry["top_entity"])

    if not skip_tx and entry.get("confidence_label") != "Reject":
        t0 = time.time()
        try:
            entry["translations"] = ts.translate(entry["caption"])
        except TranslationException:
            entry["translations"] = {}
        entry["translation_latency_ms"] = round((time.time() - t0) * 1000, 2)
    else:
        entry["translation_latency_ms"] = 0

    entry["total_latency_ms"] = round(
        sum(
            [
                entry["caption_latency_ms"],
                entry["embedding_latency_ms"],
                entry["retrieval_latency_ms"],
                entry["grounding_latency_ms"],
                entry["translation_latency_ms"],
            ]
        ),
        2,
    )
    entry["failure_type"] = classify_failure(entry)
    return entry


def write_reports(results, categories, failure_counts, total_images, args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "failure_gallery").mkdir(exist_ok=True)

    # JSON report
    with open(OUTPUT_DIR / "evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  -> {OUTPUT_DIR / 'evaluation_report.json'}")

    # CSV
    with open(OUTPUT_DIR / "benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "filename", "category", "caption", "clip_score", "gt_score",
                "word_count", "unique_ratio", "top_score", "top_entity",
                "confidence_label", "failure_type", "caption_lat_ms",
                "embed_lat_ms", "retrieval_lat_ms", "ground_lat_ms",
                "trans_lat_ms", "total_lat_ms",
            ]
        )
        for r in results:
            w.writerow(
                [
                    r["filename"], r["category"], r["caption"], r["clip_score"],
                    r.get("gt_score", ""), r["caption_word_count"],
                    r["unique_word_ratio"], r["top_score"], r["top_entity"],
                    r["confidence_label"], r.get("failure_type", ""),
                    r["caption_latency_ms"], r["embedding_latency_ms"],
                    r["retrieval_latency_ms"], r["grounding_latency_ms"],
                    r["translation_latency_ms"], r["total_latency_ms"],
                ]
            )
    print(f"  -> {OUTPUT_DIR / 'benchmark_results.csv'}")

    # Markdown summary
    lines = []
    lines.append("# OmniVision Evaluation Report\n")
    lines.append(f"**Dataset:** {total_images} images | **Model:** {args.model} | **Date:** 2026-07-28\n")
    lines.append("---\n")
    lines.append("## Category Results\n")
    header = "| Category | Count | Avg Score | Accept% | Avg Lat(ms) | Top Failure |"
    sep = "|---|---|---|---|---|---|"
    lines.append(header + "\n")
    lines.append(sep + "\n")
    for cat in sorted(categories.keys()):
        c = categories[cat]
        avg_s = sum(c["scores"]) / len(c["scores"]) if c["scores"] else 0
        avg_l = sum(c["latencies"]) / len(c["latencies"]) if c["latencies"] else 0
        ap = c["accepted"] / c["count"] * 100 if c["count"] else 0
        tf = max(set(c["failures"]), key=c["failures"].count) if c["failures"] else "-"
        lines.append(f"| {cat} | {c['count']} | {avg_s:.4f} | {ap:.0f}% | {avg_l:.1f} | {tf} |\n")
    lines.append("\n## Pipeline Metrics\n")
    lines.append("| Stage | Avg (ms) | Max (ms) |\n|---|---|---|\n")
    stages = [
        "caption_latency_ms", "embedding_latency_ms", "retrieval_latency_ms",
        "grounding_latency_ms", "translation_latency_ms",
    ]
    labels = ["Caption", "Embedding", "Retrieval", "Grounding", "Translation"]
    for lbl, k in zip(labels, stages):
        v = [r[k] for r in results]
        a = sum(v) / len(v) if v else 0
        m = max(v) if v else 0
        lines.append(f"| {lbl} | {a:.1f} | {m:.1f} |\n")
    lines.append("\n## Failure Analysis\n")
    lines.append("| Failure Type | Count | % of Images |\n|---|---|---|\n")
    for ft, cnt in sorted(failure_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {ft} | {cnt} | {cnt / total_images * 100:.1f}% |\n")
    nf = sum(1 for r in results if not r.get("failure_type"))
    lines.append(f"| no_failure | {nf} | {nf / total_images * 100:.1f}% |\n")
    lines.append("\n## Root Cause Analysis\n")
    se = sum(1 for r in results if r.get("stage_error"))
    if se > 0:
        lines.append(f"- **Implementation:** PARTIAL — {se}/{total_images} stage errors\n")
    else:
        lines.append("- **Implementation:** PASS — All images processed without errors\n")
    low_cats = []
    for cat, c in categories.items():
        avg_s = sum(c["scores"]) / len(c["scores"]) if c["scores"] else 0
        if avg_s < 0.3 and c["count"] >= 3:
            low_cats.append(f"{cat}({avg_s:.3f})")
    if low_cats:
        lines.append(f"- **Caption Model:** LIMITED — Failing: {', '.join(low_cats)}\n")
    else:
        lines.append("- **Caption Model:** PASS\n")
    re = sum(1 for r in results if not r.get("retrieval_results"))
    if re > 0:
        lines.append(f"- **Retrieval:** ISSUE — {re} images had no retrieval\n")
    else:
        lines.append("- **Retrieval:** PASS\n")
    tx_vals = [r["translation_latency_ms"] for r in results]
    tx_avg = sum(tx_vals) / len(tx_vals) if tx_vals else 0
    tx_max = max(tx_vals) if tx_vals else 0
    if tx_max > 10000:
        lines.append(f"- **Translation:** SLOW — avg {tx_avg/1000:.1f}s, max {tx_max/1000:.1f}s\n")
    else:
        lines.append("- **Translation:** PASS\n")
    lines.append("\n## Recommendation\n")
    lines.append("No production changes until bottleneck is confirmed by evidence.\n")
    with open(OUTPUT_DIR / "evaluation_summary.md", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"  -> {OUTPUT_DIR / 'evaluation_summary.md'}")

    # model_comparison.csv stub
    with open(OUTPUT_DIR / "model_comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "avg_clip_score", "avg_latency_ms", "accept_rate", "failure_rate"])
        all_scores = [r["clip_score"] for r in results]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        all_lats = [r["total_latency_ms"] for r in results]
        avg_lat = sum(all_lats) / len(all_lats) if all_lats else 0
        accept = sum(1 for r in results if r.get("confidence_label") in ("High", "Medium"))
        fail = sum(1 for r in results if r.get("failure_type"))
        w.writerow([
            args.model, round(avg_score, 4), round(avg_lat, 1),
            f"{accept/total_images*100:.1f}%" if total_images else "0%",
            f"{fail/total_images*100:.1f}%" if total_images else "0%",
        ])
    print(f"  -> {OUTPUT_DIR / 'model_comparison.csv'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="blip", help="Caption model to evaluate")
    parser.add_argument("--skip-translation", action="store_true")
    parser.add_argument("--generate-template", action="store_true")
    parser.add_argument("--max-images", type=int, default=0)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "failure_gallery").mkdir(exist_ok=True)

    images = collect_images()
    print(f"Found {len(images)} images\n")

    if args.generate_template:
        gt = {}
        for img in images:
            rel = os.path.relpath(img["path"], str(TEST_IMAGES_DIR))
            gt[rel] = ""
        with open(GROUND_TRUTH_PATH, "w", encoding="utf-8") as f:
            json.dump(gt, f, indent=2, ensure_ascii=False)
        print(f"Ground truth template written to {GROUND_TRUTH_PATH}")
        return

    gt = {}
    if GROUND_TRUTH_PATH.exists():
        with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
            gt = json.load(f)
        filled = sum(1 for v in gt.values() if v)
        if filled:
            print(f"Ground truth: {filled}/{len(gt)} filled\n")

    if args.max_images > 0:
        images = images[: args.max_images]

    print("Loading models (first load may take a minute)...")
    mm = get_model_manager()
    cs = CaptionService()
    es = EmbeddingService()
    rs = RetrievalService()
    gs = GroundingService()
    ts = TranslationService()
    print(f"  Device: {mm.device}")
    print(f"  Caption: {settings.BLIP_MODEL}")
    print(f"  CLIP: {settings.CLIP_MODEL}")
    print(f"  Translation: {settings.TRANSLATION_MODEL}\n")

    rs.warm_up()

    services = (cs, es, rs, gs, ts)
    results = []
    cats = defaultdict(
        lambda: {"count": 0, "scores": [], "accepted": 0, "latencies": [], "failures": []}
    )
    fcounts = defaultdict(int)

    for i, img in enumerate(images):
        print(f"[{i+1}/{len(images)}] [{img['category']}] {img['filename']}...", end=" ", flush=True)
        t0 = time.time()
        entry = eval_image(mm, services, img, gt, args.skip_translation)
        et = time.time() - t0
        results.append(entry)
        c = img["category"]
        cats[c]["count"] += 1
        cats[c]["scores"].append(entry.get("clip_score", 0))
        cats[c]["latencies"].append(entry["total_latency_ms"])
        if entry.get("confidence_label") in ("High", "Medium"):
            cats[c]["accepted"] += 1
        if entry.get("failure_type"):
            cats[c]["failures"].append(entry["failure_type"])
            fcounts[entry["failure_type"]] += 1
        cp = (entry["caption"] or "")[:60]
        fail_mark = f" FAIL: {entry['failure_type']}" if entry.get("failure_type") else ""
        print(f"{cp}  | score={entry.get('clip_score', 0):.3f}  | {et:.1f}s{fail_mark}")

    # Category summary
    print("\n\n==================== CATEGORY RESULTS ====================")
    print(f"{'Category':<20} {'Count':<6} {'Avg Score':<10} {'Accept%':<8} {'Avg Lat(ms)':<12} {'Top Failure':<20}")
    print("-" * 80)
    for cat in sorted(cats.keys()):
        c = cats[cat]
        avg_s = sum(c["scores"]) / len(c["scores"]) if c["scores"] else 0
        avg_l = sum(c["latencies"]) / len(c["latencies"]) if c["latencies"] else 0
        ap = c["accepted"] / c["count"] * 100 if c["count"] else 0
        tf = max(set(c["failures"]), key=c["failures"].count) if c["failures"] else "-"
        print(f"{cat:<20} {c['count']:<6} {avg_s:<10.4f} {ap:<7.0f}% {avg_l:<12.1f} {tf:<20}")

    # Failure analysis
    print("\n\n==================== FAILURE ANALYSIS ====================")
    total = len(results)
    print(f"{'Failure Type':<25} {'Count':<6} {'%':<8}")
    print("-" * 40)
    for ft, cnt in sorted(fcounts.items(), key=lambda x: -x[1]):
        print(f"{ft:<25} {cnt:<6} {cnt/total*100:<7.1f}%")
    nf = sum(1 for r in results if not r.get("failure_type"))
    print(f"{'no_failure':<25} {nf:<6} {nf/total*100:<7.1f}%")

    # Pipeline latency
    print("\n\n==================== PIPELINE METRICS ====================")
    stages = [
        "caption_latency_ms", "embedding_latency_ms", "retrieval_latency_ms",
        "grounding_latency_ms", "translation_latency_ms",
    ]
    labels = ["Caption", "Embedding", "Retrieval", "Grounding", "Translation"]
    print(f"{'Stage':<15} {'Avg (ms)':<12} {'Max (ms)':<12}")
    print("-" * 40)
    for lbl, k in zip(labels, stages):
        v = [r[k] for r in results]
        avg_v = sum(v) / len(v) if v else 0
        max_v = max(v) if v else 0
        print(f"{lbl:<15} {avg_v:<12.1f} {max_v:<12.1f}")

    write_reports(results, cats, fcounts, total, args)


if __name__ == "__main__":
    main()
