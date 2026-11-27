"""공부 위키의 '모아보기' 페이지를 study/ 안의 원본 페이지에서 다시 만든다.

실행: python3 scripts/study_rebuild.py

원본(직접 쓰는 페이지)
- study/chinese/중국어 Day NN.md, 중국어 심화 문장.md
- study/japanese/일본어 Day NN.md
- study/english-ec/영어 EC 단어 NN ….md, 영어 EC 문법 NN ….md
- study/english-biz/비즈니스 영어 표현.md (매일 한 줄씩 추가하는 표)

다시 만드는 페이지 (손으로 고치지 않는다)
- 언어별 첫 페이지(허브), 중국어 단어장, 중국어 문법 모음, 일본어 전체 단어
- Day 페이지 맨 아래 '## 관련' (이전·다음 링크)
- study/index.md (공부 위키 목차)

내용이 같으면 파일을 다시 쓰지 않는다. Python 3.9에서 동작한다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "study"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)

LANGS = [
    ("chinese", "중국어"),
    ("japanese", "일본어"),
    ("english-ec", "영어 EC"),
    ("english-biz", "영어 비즈니스·업무"),
]


# ---------- 공용 ----------

def read(path: Path) -> tuple:
    raw = path.read_text(encoding="utf-8")
    meta = {}
    m = FRONT_RE.match(raw)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        raw = raw[m.end():]
    return meta, raw


def front(title: str, cat: str, updated: str, order: int) -> str:
    lines = ["---", "title: " + title, "category: " + cat]
    if updated:
        lines.append("updated: " + updated)
    lines += ["order: %d" % order, "---", "", ""]
    return "\n".join(lines)


def write(path: Path, content: str) -> bool:
    content = re.sub(r"\n{3,}", "\n\n", content).rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def split_row(line: str) -> list:
    cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [c.strip() for c in cells]


def tables(body: str) -> list:
    """본문의 표들을 [(바로 위 제목, [행...])] 로. 첫 행이 머리글."""
    out, cur, head = [], None, ""
    for line in body.splitlines():
        if line.startswith("#"):
            head = line.lstrip("#").strip()
        if line.strip().startswith("|"):
            if re.match(r"^\|\s*-", line.strip()):
                continue
            if cur is None:
                cur = (head, [])
                out.append(cur)
            cur[1].append(split_row(line))
        else:
            cur = None
    return out


def md_table(rows: list) -> list:
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    return (["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
            + ["| " + " | ".join(r) + " |" for r in rows[1:]])


def day_pages(d: str, prefix: str) -> list:
    """[(번호, 제목, 경로, 메타, 본문)] 번호 순"""
    out = []
    for f in (STUDY / d).glob("%s Day *.md" % prefix):
        m = re.search(r"Day (\d+)$", f.stem)
        if m:
            meta, body = read(f)
            out.append((int(m.group(1)), f.stem, f, meta, body))
    return sorted(out)


def day_date(meta: dict, body: str) -> str:
    m = re.search(r"^- 날짜: (.+)$", body, re.M)
    return m.group(1).strip() if m else meta.get("updated", "")


def set_related(path: Path, meta: dict, body: str, links: list) -> bool:
    body = re.split(r"\n## 관련\n", body)[0].rstrip()
    body += "\n\n## 관련\n" + "\n".join(links) + "\n"
    return write(path, front(meta.get("title", path.stem), meta["category"], meta.get("updated", ""),
                             int(meta.get("order", "1"))) + body.lstrip("\n"))


def nav_links(hub: str, days: list, i: int) -> list:
    links = ["- [[%s]]" % hub]
    nav = []
    if i > 0:
        nav.append("이전: [[%s]]" % days[i - 1][1])
    if i + 1 < len(days):
        nav.append("다음: [[%s]]" % days[i + 1][1])
    if nav:
        links.append("- " + " · ".join(nav))
    return links


# ---------- 중국어 ----------

def grammar_items(title: str, body: str) -> list:
    """'- 문법:' 아래 하위 항목들"""
    out, cur, in_gram = [], "", False
    for line in body.splitlines():
        if line.startswith("## "):
            cur, in_gram = line[3:].strip(), False
        elif line.startswith("- 문법"):
            in_gram = True
        elif in_gram and line.startswith("    - "):
            out.append((title, cur, line[6:].strip()))
        elif not line.startswith("    "):
            in_gram = False
    return out


def chinese() -> int:
    d, hub = "chinese", "비즈니스 중국어 노트"
    days = day_pages(d, "중국어")
    changed = 0
    vocab, grammar, listing = [], [], []
    for i, (n, title, path, meta, body) in enumerate(days):
        changed += set_related(path, meta, body, nav_links(hub, days, i))
        heads = [l[3:].strip() for l in body.splitlines()
                 if l.startswith("## ") and l[3:].strip() not in ("주요 단어", "관련")]
        listing.append((title, day_date(meta, body), heads))
        grammar += grammar_items(title, body)
        for head, rows in tables(body):
            if rows and rows[0][0] == "단어":
                vocab += [(r, title) for r in rows[1:]]
    extra = sorted(f.stem for f in (STUDY / d).glob("*.md")
                   if f.stem not in {x[1] for x in days} | {hub, "중국어 단어장", "중국어 문법 모음"})
    for t in extra:
        f = STUDY / d / (t + ".md")
        meta, body = read(f)
        grammar += grammar_items(t, body)
        for head, rows in tables(body):
            if rows and rows[0][0] == "단어":
                vocab += [(r, t) for r in rows[1:]]
    last = max((x[1][:10] for x in listing if x[1]), default="")

    # 단어장
    seen, rows = set(), [["단어", "병음", "뜻", "처음 나온 곳"]]
    for r, src in vocab:
        if r[0] in seen:
            continue
        seen.add(r[0])
        rows.append((r + ["", "", ""])[:3] + ["[[%s]]" % src])
    body = ["# 중국어 단어장", "", "Day 페이지의 '주요 단어'를 모았습니다. 같은 단어는 처음 나온 곳만 적습니다. (%d개)" % (len(rows) - 1), ""]
    body += md_table(rows) + ["", "## 관련", "- [[%s]]" % hub]
    changed += write(STUDY / d / "중국어 단어장.md", front("중국어 단어장", d, last, 2) + "\n".join(body))

    # 문법 모음
    body = ["# 중국어 문법 모음", "", "Day 페이지의 문법 설명을 순서대로 모았습니다.", ""]
    cur = None
    for src, head, item in grammar:
        if src != cur:
            body += ["", "## [[%s]]" % src, ""]
            cur = src
        body.append("- " + item)
    body += ["", "## 관련", "- [[%s]]" % hub]
    changed += write(STUDY / d / "중국어 문법 모음.md", front("중국어 문법 모음", d, last, 2) + "\n".join(body))

    # 허브
    body = ["# " + hub, "",
            "하루 두 문장씩, 실제 업무 대화·메일과 일상에서 바로 쓸 수 있는 중국어 문장을 모읍니다. "
            "각 문장은 중국어 · 병음 · 뜻 · 문법 순서로 정리하고, 새 문장은 날짜별 Day 페이지로 추가합니다.", "",
            "- 모아보기: [[중국어 단어장]] · [[중국어 문법 모음]]" + "".join(" · [[%s]]" % t for t in extra), ""]
    for title, date, heads in listing:
        body.append("- [[%s]]%s" % (title, " — " + date if date else ""))
        body += ["    - " + h for h in heads]
    changed += write(STUDY / d / (hub + ".md"), front(hub, d, last, 0) + "\n".join(body))
    return changed


# ---------- 일본어 ----------

def japanese() -> int:
    d, hub, allw = "japanese", "일본어 단어장", "일본어 전체 단어"
    days = day_pages(d, "일본어")
    changed = 0
    groups, listing = {}, []
    for i, (n, title, path, meta, body) in enumerate(days):
        changed += set_related(path, meta, body, nav_links(hub, days, i))
        words = []
        for head, rows in tables(body):
            if rows and rows[0][0] in ("한자", "가타카나"):
                groups.setdefault(tuple(rows[0]), []).extend((r, title) for r in rows[1:])
                words += [r[0] for r in rows[1:]]
        listing.append((title, day_date(meta, body), words))
    last = max((x[1][:10] for x in listing if x[1]), default="")

    body = ["# " + allw, "", "Day 페이지의 단어를 한곳에 모았습니다. 같은 단어는 처음 나온 곳만 적습니다.", ""]
    for head in sorted(groups, key=lambda h: 0 if h[0] == "한자" else 1):
        seen, rows = set(), [list(head) + ["처음 나온 곳"]]
        for r, src in groups[head]:
            if r[0] in seen:
                continue
            seen.add(r[0])
            rows.append((r + [""] * len(head))[:len(head)] + ["[[%s]]" % src])
        body += ["## %s (%d개)" % (head[0], len(rows) - 1), ""] + md_table(rows) + [""]
    body += ["## 관련", "- [[%s]]" % hub]
    changed += write(STUDY / d / (allw + ".md"), front(allw, d, last, 2) + "\n".join(body))

    body = ["# " + hub, "",
            "매일 한자어 3개(한자 · 히라가나 · 로마자 · 뜻)와 가타카나어 2개(가타카나 · 로마자 · 뜻)를 "
            "날짜별 Day 페이지로 추가합니다. 일상에서 자주 쓰는 단어 위주로 고릅니다.", "",
            "- 모아보기: [[%s]]" % allw, ""]
    for title, date, words in listing:
        body.append("- [[%s]]%s" % (title, " — " + date if date else ""))
        if words:
            body.append("    - " + ", ".join(words))
    changed += write(STUDY / d / (hub + ".md"), front(hub, d, last, 0) + "\n".join(body))
    return changed


# ---------- 영어 EC ----------

def english_ec() -> int:
    d, hub = "english-ec", "영어 EC 공부 노트"
    pages = sorted(f for f in (STUDY / d).glob("*.md") if f.stem != hub)
    body = ["# " + hub, "",
            "주제별로 묶어 정리합니다. ★는 직접 올린 단어·문법이고, 나머지는 함께 알아두면 좋은 관련 단어·문법입니다.", "",
            "- 단어: 주제별 표. 단어, 뜻, 메모(헷갈리는 점·업무에서 쓰는 뜻)",
            "- 문법: 비슷한 문법끼리 묶어 형태와 예문 1개씩", ""]
    for group, prefix in (("단어", "영어 EC 단어 "), ("문법", "영어 EC 문법 ")):
        items = [f for f in pages if f.stem.startswith(prefix)]
        if not items:
            continue
        body += ["", "## " + group, ""]
        for f in items:
            meta, b = read(f)
            firsts = [r[0] for _, rows in tables(b) for r in rows[1:] if r and r[0]]
            body.append("- [[%s]]" % f.stem)
            if firsts:
                body.append("    - " + ", ".join(firsts))
    others = [f for f in pages if not f.stem.startswith(("영어 EC 단어 ", "영어 EC 문법 "))]
    if others:
        body += ["", "## 기타", ""] + ["- [[%s]]" % f.stem for f in others]
    return write(STUDY / d / (hub + ".md"), front(hub, d, "", 0) + "\n".join(body))


# ---------- 영어 비즈니스·업무 ----------

def english_biz() -> int:
    d, hub, daily = "english-biz", "업무 영어 공부 노트", "비즈니스 영어 표현"
    rows = []
    f = STUDY / d / (daily + ".md")
    if f.exists():
        meta, b = read(f)
        for head, t in tables(b):
            if t and t[0][0] == "Day":
                rows = t[1:]
        last = max((r[1] for r in rows if len(r) > 1 and DATE_RE.match(r[1])), default="")
        # 비즈니스 영어 표현 페이지의 updated 맞추기
        changed = write(f, front(daily, d, last, 1) + b.lstrip("\n"))
    else:
        last, changed = "", 0
    others = sorted(x.stem for x in (STUDY / d).glob("*.md") if x.stem not in (hub, daily))
    body = ["# " + hub, "",
            "업무 메일·회의·메신저에서 바로 쓰는 영어 표현과 문법을 모읍니다.", "",
            "- 매일 1개: 업무에서 자주 쓰는 표현 하나를 뜻 · 쓰임·주의 · 예문(해석) 순서로 [[%s]]에 추가합니다." % daily,
            "- 단어·문법: 주제별 페이지로 정리합니다.", "",
            "## 매일 비즈니스 표현 (%d개)" % len(rows), ""]
    for r in sorted(rows, key=lambda r: int(r[0]) if r[0].isdigit() else 0, reverse=True)[:7]:
        body.append("- Day %s (%s) **%s** — %s" % (r[0], r[1], r[2], r[3]))
    if not rows:
        body.append("아직 등록된 표현이 없습니다.")
    body += ["", "→ 전체: [[%s]]" % daily]
    if others:
        body += ["", "## 주제별 페이지", ""] + ["- [[%s]]" % t for t in others]
    changed += write(STUDY / d / (hub + ".md"), front(hub, d, last, 0) + "\n".join(body))
    return changed


# ---------- 목차 ----------

def index() -> int:
    lines = ["# 공부 위키 목차", "", "중국어·일본어·영어 공부 노트를 모은 위키입니다. 매일 새 내용이 추가됩니다.", ""]
    for d, label in LANGS:
        files = sorted((STUDY / d).glob("*.md")) if (STUDY / d).exists() else []
        if not files:
            continue
        hubs = [f.stem for f in files if read(f)[0].get("order") == "0"]
        lines += ["## %s (%d쪽)" % (label, len(files)), ""] + ["- [[%s]]" % h for h in hubs] + [""]
    return write(STUDY / "index.md", "\n".join(lines))


def main() -> None:
    n = chinese() + japanese() + english_ec() + english_biz() + index()
    print("공부 위키 모아보기 갱신: 바뀐 파일 %d개" % n)


if __name__ == "__main__":
    main()
