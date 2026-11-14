"""Bring catalogs you found by hand into the pipeline.

Add a row to data/manual_catalogs.csv:
  school_id      - from data/schools.csv
  catalog_url    - link to the catalog (PDF, Google Doc, Drive file or webpage)   } give either
  local_file     - OR a file you uploaded to catalogs/<school_id>/ (path in repo)   } or both
  school_year    - e.g. 2026-27
  catalog_status - optional (default "found"); e.g. partial, outdated_only, no_public_catalog
  notes          - anything worth knowing
  added_on       - YYYY-MM-DD (optional)

This script downloads the file if needed and writes/updates phase1/results/<school_id>.json with
source "manual" and today's retrieved_on date. Rows already ingested (same URL/file) are skipped.
Then run scripts/phase2_queue.py — the school will show up as ready for extraction.

Run:  python3 -I scripts/ingest_manual.py
"""
import csv, datetime, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.date.today().isoformat()


def download(url, dest_dir, year):
    m = re.search(r"docs\.google\.com/document/d/([A-Za-z0-9_-]{20,})", url)
    if m and "/d/e/" not in url:
        url, ext = f"https://docs.google.com/document/d/{m.group(1)}/export?format=pdf", "pdf"
    elif (m := re.search(r"drive\.google\.com/(?:file/d/|open\?id=)([A-Za-z0-9_-]{20,})", url)):
        url, ext = f"https://drive.google.com/uc?export=download&id={m.group(1)}", None
    else:
        ext = None
    tmp = dest_dir / "_download.tmp"
    subprocess.run(["curl", "-sSL", "--max-time", "120", "--max-filesize", str(50 * 1024 * 1024),
                    "-o", str(tmp), url], check=True)
    head = tmp.read_bytes()[:5]
    ext = ext or ("pdf" if head.startswith(b"%PDF") else "html")
    if ext == "pdf" and not head.startswith(b"%PDF"):
        raise RuntimeError("expected a PDF but got something else (sign-in page?)")
    dest = dest_dir / f"catalog_{year or 'unknown'}_manual.{ext}"
    tmp.rename(dest)
    return dest


def pdf_pages(path):
    try:
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
        return int(re.search(r"Pages:\s+(\d+)", out).group(1))
    except Exception:
        return None


def main():
    schools = {r["school_id"]: r for r in csv.DictReader((ROOT / "data/schools.csv").open())}
    rows = list(csv.DictReader((ROOT / "data/manual_catalogs.csv").open()))
    for row in rows:
        sid = row["school_id"].strip()
        if not sid:
            continue
        if sid not in schools:
            print(f"SKIP {sid}: not in data/schools.csv")
            continue
        url, local = row.get("catalog_url", "").strip(), row.get("local_file", "").strip()
        rp = ROOT / "phase1/results" / f"{sid}.json"
        r = json.loads(rp.read_text()) if rp.exists() else {"school_id": sid,
                                                             "school_name": schools[sid]["school_name"]}
        done = r.get("manual_sources") or []
        if any(d.get("url") == url and d.get("local_file") == local for d in done):
            continue
        dest_dir = ROOT / "catalogs" / sid
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            path = (ROOT / local) if local else download(url, dest_dir, row.get("school_year"))
            if not path.exists():
                raise FileNotFoundError(local)
        except Exception as e:
            print(f"FAIL {sid}: {e}")
            continue
        rel = str(path.relative_to(ROOT))
        copy = {"path": rel, "year": row.get("school_year") or None, "retrieved_on": TODAY,
                "pages": pdf_pages(path) if rel.endswith(".pdf") else None, "source": "manual"}
        r["local_copies"] = [copy] + [c for c in r.get("local_copies") or [] if c.get("path") != rel]
        r.update(catalog_status=row.get("catalog_status") or "found", catalog_url=url or r.get("catalog_url"),
                 school_year=row.get("school_year") or r.get("school_year"), retrieved_on=TODAY,
                 checked_on=TODAY, confidence="high")
        r["issues"] = ((r.get("issues") or "") + f" [Manual {TODAY}: {row.get('notes','')}]").strip()
        r["manual_sources"] = done + [{"url": url, "local_file": local, "ingested_on": TODAY}]
        rp.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
        print(f"OK   {sid}: {rel}")


if __name__ == "__main__":
    main()
