"""Convert a school's primary catalog copy to plain text with page markers, for the extraction agent.

Output: phase2/text/<school_id>.txt  with lines "=== PAGE n ===" before each page (PDF) or
        "=== SECTION ===" blocks (HTML). Prints page count and flags pages with little text
        (likely scanned images -> the agent should read those pages from the PDF directly).

Run:  python3 -I scripts/extract_text.py <school_id> [path-to-specific-copy]
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pick_copy(r):
    copies = r.get("local_copies") or []
    year = r.get("school_year")
    same_year = [c for c in copies if c.get("year") == year]
    pool = same_year or copies
    # prefer PDF over HTML, then manual over agent-found, then newest retrieval
    pool = sorted(pool, key=lambda c: c.get("retrieved_on") or "", reverse=True)
    pool.sort(key=lambda c: (not c["path"].endswith(".pdf"), c.get("source") != "manual"))
    return pool[0] if pool else None


def pdf_text(path):
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True).stdout
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def html_text(path):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(path.read_text(errors="replace"), "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    text = soup.get_text("\n")
    lines = [l.strip() for l in text.splitlines()]
    text = "\n".join(l for l in lines if l)
    chunk = 6000
    return [text[i:i + chunk] for i in range(0, len(text), chunk)] or [""]


def main():
    sid = sys.argv[1]
    r = json.loads((ROOT / "phase1/results" / f"{sid}.json").read_text())
    copy = {"path": sys.argv[2]} if len(sys.argv) > 2 else pick_copy(r)
    if not copy:
        sys.exit(f"{sid}: no local copy")
    path = ROOT / copy["path"]
    pages = pdf_text(path) if path.suffix.lower() == ".pdf" else html_text(path)
    label = "PAGE" if path.suffix.lower() == ".pdf" else "SECTION"
    out = ROOT / "phase2/text" / f"{sid}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for i, p in enumerate(pages, 1):
            f.write(f"=== {label} {i} ===\n{p}\n")
    low = [i for i, p in enumerate(pages, 1) if len(p.strip()) < 200]
    print(json.dumps({"school_id": sid, "source": copy["path"], "retrieved_on": copy.get("retrieved_on"),
                      "year": copy.get("year"), "units": len(pages), "unit_type": label.lower(),
                      "chars": sum(len(p) for p in pages), "low_text_units": low, "text_file": str(out.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
