"""Convert a school's current catalog file(s) to plain text with markers, for the extraction agent.

Uses every local copy named catalog_* for the school's primary school_year (e.g. a main Program of Studies
plus a separate 9th-grade guide). For each year, prefers a manual copy, then PDF over HTML.
Graduation-requirement files (grad_requirements_*) are listed separately and not converted.

Output: phase2/text/<school_id>.txt with "=== FILE <path> ===" headers and "=== PAGE n ===" (PDF) or
        "=== SECTION n ===" (HTML) markers. Prints a JSON summary including source_retrieved_on and
        low_text_units (pages with little text -> probably scanned; read those from the PDF directly).

Run:  python3 -I scripts/extract_text.py <school_id> [specific/copy/path ...]
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pick_copies(r):
    copies = [c for c in r.get("local_copies") or [] if (ROOT / c.get("path", "")).exists()]
    cats = [c for c in copies if Path(c["path"]).name.startswith("catalog")]
    year = r.get("school_year")
    pool = [c for c in cats if c.get("year") == year] or cats
    # same document saved as both PDF and HTML -> keep the PDF; keep distinct documents
    chosen, stems = [], set()
    pool = sorted(pool, key=lambda c: (c.get("source") != "manual", not c["path"].endswith(".pdf")))
    for c in pool:
        stem = re.sub(r"(_published)?\.(pdf|html?)$", "", Path(c["path"]).name)
        if stem in stems:
            continue
        stems.add(stem)
        chosen.append(c)
    grad = [c["path"] for c in copies if Path(c["path"]).name.startswith("grad")]
    return chosen, grad


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
    lines = [l.strip() for l in soup.get_text("\n").splitlines()]
    text = "\n".join(l for l in lines if l)
    return [text[i:i + 6000] for i in range(0, len(text), 6000)] or [""]


def main():
    sid = sys.argv[1]
    r = json.loads((ROOT / "phase1/results" / f"{sid}.json").read_text())
    if len(sys.argv) > 2:
        copies = [{"path": p, "retrieved_on": r.get("retrieved_on")} for p in sys.argv[2:]]
        grad = []
    else:
        copies, grad = pick_copies(r)
    if not copies:
        sys.exit(f"{sid}: no local catalog copy")
    out = ROOT / "phase2/text" / f"{sid}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = []
    with out.open("w") as f:
        for c in copies:
            path = ROOT / c["path"]
            is_pdf = path.suffix.lower() == ".pdf"
            units = pdf_text(path) if is_pdf else html_text(path)
            label = "PAGE" if is_pdf else "SECTION"
            f.write(f"=== FILE {c['path']} ===\n")
            for i, u in enumerate(units, 1):
                f.write(f"=== {label} {i} ===\n{u}\n")
            files.append({"path": c["path"], "year": c.get("year"), "retrieved_on": c.get("retrieved_on"),
                          "units": len(units), "unit_type": label.lower(), "chars": sum(map(len, units)),
                          "low_text_units": [i for i, u in enumerate(units, 1) if len(u.strip()) < 200]})
    dates = [x["retrieved_on"] for x in files if x.get("retrieved_on")]
    print(json.dumps({"school_id": sid, "source_files": [x["path"] for x in files],
                      "source_retrieved_on": max(dates) if dates else r.get("retrieved_on"),
                      "files": files, "grad_requirement_files": grad,
                      "text_file": str(out.relative_to(ROOT))}, indent=1))


if __name__ == "__main__":
    main()
