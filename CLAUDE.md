# 공부 위키 운영 규칙

이 폴더(공부위키)는 중국어·일본어·영어 공부 노트를 모은 공부 위키다. 저장소는 LillyPark99/Lilly1 (공개). 웹 주소: https://lillypark99.github.io/Lilly1/
공부 노트가 아닌 자료(회사 업무 자료 등)는 이 폴더에 넣지 않는다.

## 구조
- study/<언어>/*.md: scripts/study_import.py가 원본 문서(Claude Docs)에서 만든 페이지. 직접 고치지 않고 원본 문서를 고친다.
- index.html: python3 scripts/build_study.py 로 만든 공부 위키 (외부 자원 없음, 파일 하나로 열림)
- scripts/auto_sync.sh: 바뀐 게 있으면 빌드 → 커밋 → push. Stop 훅(.claude/settings.json)과 예약 작업에서 실행.

## 원본 문서
| 키 | 문서 | 문서 id | 본문 node id |
|---|---|---|---|
| zh | 비즈니스 중국어 노트 | c8f9fb88-6011-4739-b195-f5bd70badab9 | 3f8a3dcc-893d |
| ja | 일본어 단어장 | d29d20e6-14bc-4b18-8849-bc09fb2d7d94 | e7e7c73e-b216 |
| en-ec | 영어 EC 공부 노트 | a0d32e5a-312b-49cb-9cc7-3f20053830fa | 64fe5433-1d83 |
| en-biz | 업무 영어 공부 노트 | 4c08802b-1100-4893-8382-25bb45d0cac4 | 6667edbc-d71c |

## 명령어
- "공부 위키 갱신": 원본 문서 4개를 Claude Docs 커넥터로 읽고(payload 없이 node read) → `python3 scripts/study_import.py <키> <파일>` → `bash scripts/auto_sync.sh`
- 매일 22:00 예약 작업 '공부 위키 동기화'(study-wiki-sync)가 같은 순서로 실행한다.

## 규칙
- 비밀번호, 인증번호, 주민번호, 계좌번호는 저장하지 않는다.
- 출력 HTML에는 외부 자원(CDN, 웹폰트, 외부 스크립트)을 쓰지 않는다.
- Python 3.9.6 (`python3`)에서 돌아가게 작성한다.
