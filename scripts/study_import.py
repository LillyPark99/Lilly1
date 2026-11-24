"""공부 노트(Claude Docs 문서)를 공부 위키 페이지(study/*.md)로 바꾼다.

실행: python3 scripts/study_import.py <원본키> <읽은 결과 파일>
  원본키: zh(비즈니스 중국어 노트), ja(일본어 단어장), en-ec(영어 EC 공부 노트), en-biz(업무 영어 공부 노트)
  읽은 결과 파일: Claude Docs connector로 문서 본문을 읽은 결과를 저장한 파일.
                  {"verdict":..., "data": {"xml": "<doc ...>"}} 형태든, <doc ...> XML만 든 파일이든 된다.

- 같은 원본에서 만든 페이지는 매번 통째로 다시 만든다 (원본 문서가 기준).
- 내용이 같으면 파일도 똑같이 나오게 만든다(빌드 시각 같은 값을 넣지 않음). 그래야 바뀐 날만 커밋된다.
- 끝나면 study/index.md(공부 위키 목차)도 다시 만든다.
- Python 3.9에서 동작한다.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "study"

SOURCES = {
    "zh": {"dir": "chinese", "lang": "중국어", "prefix": "중국어", "split": 2,
           "url": "https://claude.ai/artifact/RpQrFKPPX4DL2W1udMjGFa"},
    "ja": {"dir": "japanese", "lang": "일본어", "prefix": "일본어", "split": 2,
           "url": "https://claude.ai/artifact/T1SByDwNYfMQnwpYAQTpjM"},
    "en-ec": {"dir": "english", "lang": "영어", "prefix": "영어 EC", "split": 3,
              "url": "https://claude.ai/artifact/Lrqr1YUK8naGPTRAEN8n4q"},
    "en-biz": {"dir": "english", "lang": "영어", "prefix": "업무 영어", "split": 3,
               "url": "https://claude.ai/artifact/APZGuviyiunBCnh7vah8ps"},
}
LANG_ORDER = [("chinese", "중국어"), ("japanese", "일본어"), ("english", "영어")]
INTRO_SECTIONS = {"정리 방식"}
VOCAB_HEADS = {"단어", "한자", "가타카나"}
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
NOTE = "> 원본 문서에서 자동으로 만든 페이지입니다. 내용은 원본에서 고치면 다음 동기화 때 반영됩니다."


# ---------- 읽기 ----------

def load_xml(path: Path) -> ET.Element:
    raw = path.read_text(encoding="utf-8")
    s = raw.lstrip()
    if not s.startswith("<doc"):
        i = raw.index("{")
        data = json.JSONDecoder().raw_decode(raw[i:])[0]
        d = data.get("data") or data.get("value", {}).get("data") or {}
        if d.get("complete") is False:
            sys.exit("문서를 끝까지 읽지 못했습니다 (complete=false). 이어 읽기 후 다시 실행하세요.")
        s = d["xml"]
    return ET.fromstring(s)


def text(el: ET.Element) -> str:
    out = []
    for e in el.iter():
        if e.tag == "text":
            out.append(e.text or "")
        elif e.tag == "date":
            out.append(e.get("value", ""))
    return "".join(out).strip()


def esc_cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def md_list(lst: ET.Element, depth: int = 0) -> list:
    out = []
    for li in lst.findall("listItem"):
        for ch in li:
            if ch.tag == "paragraph" and text(ch):
                out.append("    " * depth + "- " + text(ch))
            elif ch.tag == "list":
                out.extend(md_list(ch, depth + 1))
    return out


def table_rows(tb: ET.Element) -> list:
    return [[text(c) for c in r.findall("cell")] for r in tb.findall("row")]


def md_table(rows: list) -> list:
    if not rows:
        return []
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    lines = ["| " + " | ".join(esc_cell(c) for c in rows[0]) + " |", "|" + "---|" * w]
    lines += ["| " + " | ".join(esc_cell(c) for c in r) + " |" for r in rows[1:]]
    return lines


# ---------- 나누기 ----------

def sections(root: ET.Element, split: int) -> tuple:
    """문서를 (머리말 블록들, [(그룹, 제목, 블록들)]) 로 나눈다."""
    intro, out = [], []
    group, cur = "", None
    for el in root:
        h = el.get("heading") if el.tag == "paragraph" else None
        lvl = int(h) if h else 0
        if lvl == 1:
            continue
        if lvl and lvl < split:  # 상위 묶음 (split=3일 때 h2)
            group = text(el)
            cur = None
            if group in INTRO_SECTIONS:
                cur = ("__intro__", group, intro)
            continue
        if lvl == split:
            cur = (group, text(el), [])
            out.append(cur)
            continue
        if cur is None:
            if group and split == 3:  # 묶음 제목 바로 아래 글 (예: "아직 등록된 표현이 없습니다.")
                out.append((group, "", [el]))
            else:
                intro.append(el)
            continue
        cur[2].append(el)
    return intro, [s for s in out if s[1] or s[2]]


def page_title(cfg: dict, group: str, title: str) -> str:
    m = re.match(r"Day\s*(\d+)", title)
    if m:
        return "%s Day %02d" % (cfg["prefix"], int(m.group(1)))
    t = re.sub(r"\s*\([^)]*\)\s*$", "", title) if cfg["split"] == 2 else title
    m = re.match(r"(\d+)\.\s*(.+)", t)
    if m:
        t = "%02d %s" % (int(m.group(1)), m.group(2))
    t = t.replace(":", " -")
    return " ".join(x for x in [cfg["prefix"], group if cfg["split"] == 3 else "", t] if x)


def render(blocks: list, split: int, coll: dict, title: str) -> list:
    lines = []
    last_head = ""
    for el in blocks:
        if el.tag == "paragraph":
            t = text(el)
            if not t:
                continue
            h = el.get("heading")
            if h:
                last_head = t
                lines += ["", "#" * max(2, int(h) - split + 1) + " " + t, ""]
            else:
                lines += ["", t, ""]
        elif el.tag == "list":
            ls = md_list(el)
            lines += [""] + ls + [""]
            for ln in ls:  # "문법:" 아래 하위 항목 모으기
                if ln.startswith("    - "):
                    coll["grammar"].append((title, last_head, ln[6:]))
        elif el.tag == "table":
            rows = table_rows(el)
            lines += [""] + md_table(rows) + [""]
            if rows and rows[0] and rows[0][0] in VOCAB_HEADS:
                coll["vocab"].setdefault(tuple(rows[0]), []).extend((r, title) for r in rows[1:])
    return lines


def first_cells(blocks: list) -> list:
    out = []
    for el in blocks:
        if el.tag == "table":
            out += [r[0] for r in table_rows(el)[1:] if r and r[0]]
    return out


def sub_heads(blocks: list) -> list:
    return [text(el) for el in blocks if el.tag == "paragraph" and el.get("heading")
            and text(el) and text(el) != "주요 단어"]


# ---------- 쓰기 ----------

def front(title: str, cat: str, key: str, updated: str, order: int) -> str:
    fm = ["---", "title: " + title, "category: " + cat, "source: " + key]
    if updated:
        fm.append("updated: " + updated)
    fm += ["order: %d" % order, "---", ""]
    return "\n".join(fm) + "\n"


def fname(title: str) -> str:
    return title.replace("/", "-")


def tidy(body: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"


def import_source(key: str, path: Path) -> None:
    cfg = SOURCES[key]
    root = load_xml(path)
    doc_title = ""
    for el in root:
        if el.tag == "paragraph" and el.get("heading") == "1":
            doc_title = text(el)
            break
    doc_title = doc_title or key
    intro, secs = sections(root, cfg["split"])
    outdir = STUDY / cfg["dir"]
    outdir.mkdir(parents=True, exist_ok=True)

    pages = {}  # 파일 제목 → 내용
    coll = {"vocab": {}, "grammar": []}
    listing = []  # 허브에 쓸 (그룹, 페이지제목, 원제목, 요약)
    group_notes = {}
    titles = [page_title(cfg, g, t) for g, t, _ in secs if t]
    ti = 0
    dates = []
    for g, t, blocks in secs:
        if not t:  # 묶음 아래 안내 글
            group_notes.setdefault(g, []).extend(render(blocks, cfg["split"], coll, ""))
            continue
        title = titles[ti]
        prev_t = titles[ti - 1] if ti > 0 else ""
        next_t = titles[ti + 1] if ti + 1 < len(titles) else ""
        ti += 1
        d = DATE_RE.search(t)
        if d:
            dates.append(d.group(0))
        body = ["# " + title, "", NOTE, "", "- 원본 제목: " + t, ""]
        body += render(blocks, cfg["split"], coll, title)
        body += ["", "## 관련", "- [[%s]]" % doc_title]
        nav = []
        if prev_t:
            nav.append("이전: [[%s]]" % prev_t)
        if next_t:
            nav.append("다음: [[%s]]" % next_t)
        if nav:
            body.append("- " + " · ".join(nav))
        pages[title] = front(title, cfg["dir"], key, d.group(0) if d else "", 1) + tidy("\n".join(body))
        heads = sub_heads(blocks)
        summary = heads if heads else [", ".join(first_cells(blocks))] if first_cells(blocks) else []
        listing.append((g, title, t, summary))

    extra = []
    if cfg["split"] == 2 and coll["vocab"]:
        vt = "%s 단어장" % cfg["prefix"]
        if vt == doc_title:
            vt = "%s 전체 단어" % cfg["prefix"]
        extra.append(vt)
        body = ["# " + vt, "", NOTE, "", "날짜별 페이지의 단어를 한곳에 모았습니다. 같은 단어는 처음 나온 곳만 적습니다.", ""]
        total = 0
        for head, rows in coll["vocab"].items():
            seen, table = set(), [list(head) + ["처음 나온 곳"]]
            for r, src in rows:
                if r[0] in seen:
                    continue
                seen.add(r[0])
                table.append(r + ["[[%s]]" % src])
            total += len(table) - 1
            body += ["## " + head[0], ""] + md_table(table) + [""]
        body += ["## 관련", "- [[%s]]" % doc_title]
        pages[vt] = front(vt, cfg["dir"], key, max(dates) if dates else "", 2) + tidy("\n".join(body))
    if coll["grammar"]:
        gt = "%s 문법 모음" % cfg["prefix"]
        extra.append(gt)
        body = ["# " + gt, "", NOTE, "", "날짜별 페이지의 문법 설명을 순서대로 모았습니다.", ""]
        cur = None
        for src, head, item in coll["grammar"]:
            if src != cur:
                body += ["", "## [[%s]]" % src, ""]
                cur = src
            body.append("- " + item)
        body += ["", "## 관련", "- [[%s]]" % doc_title]
        pages[gt] = front(gt, cfg["dir"], key, max(dates) if dates else "", 2) + tidy("\n".join(body))

    # 허브 페이지
    hub = ["# " + doc_title, ""]
    for el in intro:
        if el.tag == "paragraph":
            t = text(el)
            if t and t.strip(" ·") and not (el.find("date") is not None and len(t) < 20):
                hub += [t, ""]
        elif el.tag == "list":
            hub += md_list(el) + [""]
    hub += ["- 원본 문서: [%s](%s) (버전 %s)" % (doc_title, cfg["url"], root.get("rev", "?"))]
    if extra:
        hub.append("- 모아보기: " + " · ".join("[[%s]]" % x for x in extra))
    hub.append("")
    cur_g = None
    for g, title, t, summary in listing:
        if cfg["split"] == 3 and g != cur_g:
            hub += ["", "## " + g, ""]
            cur_g = g
        label = re.sub(r"^Day\s*\d+\s*[·—-]?\s*", "", t) if cfg["split"] == 2 else ""
        hub.append("- [[%s]]%s" % (title, " — " + label if label and label != title else ""))
        for s in summary[:4]:
            hub.append("    - " + s)
    for g, notes in group_notes.items():
        if not any(g == x[0] for x in listing):
            hub += ["", "## " + g, ""] + [n for n in notes if n]
    if not listing and not group_notes:
        hub += ["", "아직 정리된 내용이 없습니다."]
    pages[doc_title] = front(doc_title, cfg["dir"], key, max(dates) if dates else "", 0) + tidy("\n".join(hub))

    # 이 원본에서 만든 예전 페이지 중 이제 없는 것 정리
    removed = 0
    for f in outdir.glob("*.md"):
        head = f.read_text(encoding="utf-8")[:300]
        if "\nsource: %s\n" % key in head and f.stem not in {fname(t) for t in pages}:
            f.unlink()
            removed += 1
    changed = 0
    for title, content in pages.items():
        f = outdir / (fname(title) + ".md")
        if not f.exists() or f.read_text(encoding="utf-8") != content:
            f.write_text(content, encoding="utf-8")
            changed += 1
    print("%s: 페이지 %d개 (바뀜 %d, 정리 %d) → study/%s/" % (doc_title, len(pages), changed, removed, cfg["dir"]))


def build_index() -> None:
    lines = ["# 공부 위키 목차", "", "중국어·일본어·영어 공부 노트를 모은 위키입니다.", ""]
    for d, label in LANG_ORDER:
        files = sorted((STUDY / d).glob("*.md")) if (STUDY / d).exists() else []
        if not files:
            continue
        hubs = []
        for f in files:
            head = f.read_text(encoding="utf-8")[:300]
            if "\norder: 0\n" in head:
                hubs.append(f.stem)
        lines += ["## %s (%d쪽)" % (label, len(files)), ""]
        lines += ["- [[%s]]" % h for h in hubs] + [""]
    out = STUDY / "index.md"
    content = "\n".join(lines).rstrip() + "\n"
    if not out.exists() or out.read_text(encoding="utf-8") != content:
        out.write_text(content, encoding="utf-8")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--index":
        build_index()
        return
    if len(sys.argv) != 3 or sys.argv[1] not in SOURCES:
        sys.exit("사용법: python3 scripts/study_import.py <%s> <파일>" % "|".join(SOURCES))
    import_source(sys.argv[1], Path(sys.argv[2]))
    build_index()


if __name__ == "__main__":
    main()
