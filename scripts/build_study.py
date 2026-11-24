"""공부 위키: study/**/*.md → index.html (저장소 첫 화면이 곧 공부 위키)

실행: python3 scripts/build_study.py
- study/ 의 md는 scripts/study_import.py가 공부 노트 원본 문서에서 만든다.
- 외부 자원 없음, Python 3.9 호환.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki  # noqa: E402

ROOT = build_wiki.ROOT
STUDY = ROOT / "study"
OUT = ROOT / "index.html"
CATEGORIES = [("chinese", "중국어"), ("japanese", "일본어"), ("english", "영어")]


def main() -> None:
    build_wiki.build(STUDY, OUT, CATEGORIES, "공부 위키", hub=None)


if __name__ == "__main__":
    main()
