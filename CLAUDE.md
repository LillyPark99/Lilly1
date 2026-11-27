# 공부 위키 운영 규칙

이 폴더(공부위키)는 중국어·일본어·영어 공부 노트를 모은 공부 위키다. 저장소는 LillyPark99/Lilly1 (공개). 웹 주소: https://lillypark99.github.io/Lilly1/
공부 노트가 아닌 자료(회사 업무 자료 등)는 이 폴더에 넣지 않는다.
따로 Claude Docs·아티팩트를 만들지 않는다. study/의 md 파일이 원본이다.

## 구조
- study/chinese/중국어 Day NN.md: 하루 두 문장 (원본)
- study/japanese/일본어 Day NN.md: 한자어 3개 + 가타카나어 2개 (원본)
- study/english-ec/영어 EC 단어|문법 NN ….md: 주제별 단어·문법 (원본, 사용자가 단어를 주면 추가)
- study/english-biz/비즈니스 영어 표현.md: 매일 1개씩 표에 한 줄 추가 (원본)
- 허브·단어장·문법 모음·전체 단어·Day 페이지의 '## 관련'·study/index.md 는 `python3 scripts/study_rebuild.py`가 만든다. 손으로 고치지 않는다.
- index.html: `python3 scripts/build_study.py`가 만드는 공부 위키 (외부 자원 없음)
- scripts/auto_sync.sh: 바뀐 게 있으면 rebuild → 빌드 → 민감정보 검사 → 커밋 → push. Stop 훅과 예약 작업에서 실행.

## 매일 추가 형식 (기존 마지막 Day 페이지를 열어 형식을 그대로 따른다)
- 중국어 Day: frontmatter(title, category: chinese, updated, order: 1) → `# 중국어 Day NN` → `- 날짜: YYYY-MM-DD (일상)` → `## 1. 문장` 아래 `- 병음:` `- 뜻:` `- 문법:`(하위 항목 2~4개, 예시 포함) → `## 2. 문장` 같은 형식 → `## 주요 단어` 표(단어 | 병음 | 뜻).
- 일본어 Day: frontmatter(category: japanese) → `# 일본어 Day NN` → `- 날짜: YYYY-MM-DD` → 표(한자 | 히라가나 | 로마자 | 뜻) 3행 → 표(가타카나 | 로마자 | 뜻) 2행.
- 비즈니스 영어: 표(Day | 날짜 | 표현 | 뜻 | 쓰임·주의 | 예문) 맨 아래에 한 줄.
- 이미 나온 단어·표현·문법은 되도록 겹치지 않게 고른다 (단어장·문법 모음·표를 먼저 확인).

## 명령어
- "공부 위키 갱신" / 매일 22:00 예약 작업 '공부 위키 매일 추가'(study-wiki-sync): 오늘 날짜 내용을 위 형식으로 추가 → `bash scripts/auto_sync.sh`
- "영어 추가: <단어·문법>": 알맞은 영어 EC 주제 페이지 표에 ★를 붙여 추가 (없으면 새 주제 페이지) → `bash scripts/auto_sync.sh`

## 규칙
- 비밀번호, 인증번호, 주민번호, 계좌번호는 저장하지 않는다.
- 출력 HTML에는 외부 자원(CDN, 웹폰트, 외부 스크립트)을 쓰지 않는다.
- Python 3.9.6 (`python3`)에서 돌아가게 작성한다.
