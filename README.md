# PrintImg

이미지 파일을 A4 세로 기준 다중 페이지 PDF로 만듭니다. 세로로 긴 화면 캡처를 종이로 뽑을 때 씁니다.

## 동작

- 이미지 폭을 인쇄 가능 영역에 100% 맞춥니다. 작으면 확대, 크면 축소.
- "원본 크기 유지"를 켜면 96 DPI 기준 실제 크기로 출력합니다. A4보다 넓으면 폭 맞춤으로 자동 전환.
- 한 페이지를 넘는 높이는 여러 페이지로 나눕니다. 페이지 경계 근처(위쪽 30% 이내)의 빈 줄에서 자르고, 없으면 등분합니다.
- "빈 줄에 맞춰 자르기"를 끄면 빈 줄 탐색 없이 등분합니다. 상태줄에 빈 줄에서 잘린 횟수가 표시됩니다.
- "배경색"을 켜면 자동 감지된 배경색(가장자리 최빈색)을 제거(흰색) 또는 흐리게 처리합니다. 색상 버튼으로 직접 고를 수 있습니다.
- 여백은 0~30 mm, 기본 10 mm.
- 페이지 수가 50페이지를 넘으면 PDF를 만들지 않고 오류 메시지를 표시합니다.
- 결과 PDF는 원본과 같은 폴더에 `<원본이름>.pdf`로 저장되고 기본 뷰어로 열립니다.
- "바로 인쇄…"는 파일을 만들지 않고 미리보기 창(페이지 썸네일, 프린터 선택)을 연 뒤 선택한 프린터로 보냅니다.

지원 형식: PNG, JPG, BMP, GIF(첫 프레임), WEBP

## 실행

```
python -m pip install -r requirements.txt
python src/main.py
```

## 테스트

```
python -m pip install -r requirements-dev.txt
python -m pytest
```

## 빌드 (Windows exe)

```
python -m pip install pyinstaller
scripts\build.bat
```

결과물: `dist\PrintImg.exe`

## 빌드 (macOS .app)

맥에서만 빌드할 수 있습니다 (PyInstaller는 크로스 빌드를 지원하지 않습니다). Tk가 포함된 Python 3.12 이상이 필요합니다. asdf·pyenv로 설치한 파이썬과 macOS 기본 `python3`(3.9, Tk 8.5)는 대개 Tk가 없거나 너무 오래되어 안 됩니다.

```
brew install python-tk@3.13
scripts/build.sh
```

`build.sh`는 Tk가 있는 파이썬을 자동으로 찾아 `.venv`를 만들고 그 안에서 빌드합니다. 다른 파이썬을 쓰려면 `PYTHON=/경로/python3 scripts/build.sh`. 개발 중에도 같은 `.venv`를 쓰면 됩니다 (`.venv/bin/python src/main.py`, `.venv/bin/python -m pytest`).

결과물: `dist/PrintImg.app` (onedir 번들, ad-hoc 서명). 처음 실행 시 "확인되지 않은 개발자" 경고가 뜨면 앱을 우클릭 → 열기.

맥에서는 "바로 인쇄…"가 CUPS(`lpstat`, `lpr`)를 씁니다. 프린터 목록이 비어 있으면 시스템 설정 → 프린터 및 스캐너에서 프린터를 먼저 추가하세요. 실제 프린터 없이 인쇄 경로를 확인하려면 macOS에 들어 있는 가상 IPP 프린터를 쓸 수 있습니다:

```
ippeveprinter -k -d /tmp/printimg-spool -p 8632 -f application/pdf "PrintImgTest" &
lpadmin -p PrintImgTest -E -v ipp://localhost:8632/ipp/print -m everywhere
```

인쇄하면 `/tmp/printimg-spool`에 프린터가 받은 PDF가 그대로 남습니다. 끝나면 `lpadmin -x PrintImgTest`.

### 맥에서 확인한 것 (2026-09-10, macOS 26.6, Apple Silicon, Python 3.13 + Tk 9.0)

- [x] `pytest` 통과
- [x] `src/main.py`로 창이 뜨고, 이미지 선택 → PDF 만들기 → 덮어쓰기 확인창 → Preview 앱이 열린다
- [x] 배경색 견본에 감지된 색이 보이고, 버튼을 누르면 시스템 색 선택창이 뜬다
- [x] "바로 인쇄…" 미리보기 창의 프린터 목록에 `lpstat -p`의 이름이 보이고, 인쇄하면 가상 프린터에 A4 3페이지 PDF가 도착한다 (임시 PDF는 지워짐)
- [x] `scripts/build.sh`로 만든 `PrintImg.app`이 실행된다
- [ ] 실제 프린터로 종이 출력 (미확인)

알려진 차이: 확인창의 버튼이 시스템 언어 설정에 따라 "Yes / No"로 나올 수 있습니다 (Tk가 시스템 대화상자를 씀).

맥에서 고친 것: 미리보기 창의 휠 스크롤이 맥에서 동작하지 않던 문제(Tk의 delta 단위가 Windows와 다름), Finder에서 실행하면 포커스가 바뀔 때까지 빈 창으로 보이던 문제(시작 직후 창을 다시 매핑), onefile+.app 조합(PyInstaller deprecated, 두 프로세스로 뜸)을 onedir로 변경.

## 릴리스 전 수동 확인

- [ ] `_data`의 샘플 캡처로 3페이지 PDF가 생성되고 뷰어가 자동으로 열린다
- [ ] 페이지 경계가 차트 중간이 아닌 카드 사이 여백에 있다
- [ ] 같은 파일로 다시 만들면 덮어쓰기 확인창이 뜬다
- [ ] PDF를 뷰어에서 연 채로 덮어쓰면 "파일이 열려 있습니다" 메시지가 뜬다
- [ ] 여백에 범위 밖 값을 넣으면 오류 메시지가 뜬다
- [ ] "원본 크기 유지"로 작은 이미지를 만들면 가운데 정렬된다
- [ ] "바로 인쇄…"로 미리보기가 뜨고, 프린터를 골라 인쇄하면 실제 종이에 A4 3장이 나온다
- [ ] "배경색" 제거로 회색 배경이 흰색으로 출력된다
- [ ] Python이 없는 PC에서 `PrintImg.exe`가 실행된다
