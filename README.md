# PrintImg

이미지 파일을 A4 세로 기준 다중 페이지 PDF로 만듭니다. 세로로 긴 화면 캡처를 종이로 뽑을 때 씁니다.

## 동작

- 이미지 폭을 인쇄 가능 영역에 100% 맞춥니다. 작으면 확대, 크면 축소.
- "원본 크기 유지"를 켜면 96 DPI 기준 실제 크기로 출력합니다. A4보다 넓으면 폭 맞춤으로 자동 전환.
- 한 페이지를 넘는 높이는 여러 페이지로 나눕니다. 페이지 경계 근처(위쪽 30% 이내)의 빈 줄에서 자르고, 없으면 등분합니다.
- 여백은 0~30 mm, 기본 10 mm.
- 결과 PDF는 원본과 같은 폴더에 `<원본이름>.pdf`로 저장되고 기본 뷰어로 열립니다.

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

## 빌드 (exe)

```
python -m pip install pyinstaller
scripts\build.bat
```

결과물: `dist\PrintImg.exe`

## 릴리스 전 수동 확인

- [ ] `_data`의 샘플 캡처로 3페이지 PDF가 생성되고 뷰어가 자동으로 열린다
- [ ] 페이지 경계가 차트 중간이 아닌 카드 사이 여백에 있다
- [ ] 같은 파일로 다시 만들면 덮어쓰기 확인창이 뜬다
- [ ] PDF를 뷰어에서 연 채로 덮어쓰면 "파일이 열려 있습니다" 메시지가 뜬다
- [ ] 여백에 범위 밖 값을 넣으면 오류 메시지가 뜬다
- [ ] "원본 크기 유지"로 작은 이미지를 만들면 가운데 정렬된다
- [ ] Python이 없는 PC에서 `PrintImg.exe`가 실행된다
