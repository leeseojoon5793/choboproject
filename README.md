# 교육용 웹 PACS: 저선량 흉부 CT 영상 품질 향상

전북대학교 초급프로젝트(AIX-PBL) 4인 팀 프로젝트입니다.
저선량 흉부 CT 영상을 웹에서 등록·조회하고, 노이즈 제거·대비 향상 알고리즘을 적용해 처리 전후를 비교하는 교육용 PACS 프로토타입입니다.

> 이 프로그램은 수업용 프로토타입이며 진단 목적으로 사용할 수 없습니다. 실제 환자 정보는 다루지 않고 공개 데이터셋만 사용합니다.

- 배포 주소: http://s.jedutools.io:50216

## 주요 기능

| 기능 | 설명 |
|---|---|
| 로그인·역할 | Firebase 이메일 로그인, 역할(등록 담당·검토 담당·관리 담당)별 권한 |
| 케이스 등록·검색 | 저선량 CT 슬라이스(PNG) 업로드, 제목·상태·담당자 조건 검색 |
| 상태 관리 | 접수 → 배정 → 검토 중 → 완료/재검토 요청, 변경 이력(`status_logs`) 기록 |
| 영상 처리 | Median·Bilateral·Gaussian 필터, CLAHE, Canny, Otsu 이진화 |
| 화질 지표 | ROI 기반 잡음 감소율·대비 보존율(정답 영상 없이 계산), 검증용 PSNR |

## 데이터

- 출처: TCIA, *Low Dose CT Image and Projection Data (LDCT-and-Projection-data)*
- DOI: 10.7937/9NPB-2637, 라이선스: CC BY 4.0
- 사용 범위: Siemens SOMATOM Definition Flash 흉부 케이스
- 전처리: DICOM → CT 값 변환(RescaleSlope·RescaleIntercept) → 창 설정(center -600, width 1500) → 8비트 PNG 512×512
- 원본 DICOM과 변환 영상은 용량과 라이선스 때문에 레포에 올리지 않습니다(`.gitignore`의 `raw_dicom/`, `processed_ct/`, `data/`).
- 일반 선량 영상은 PSNR 검증 실험에서만 사용하고, 앱 DB에는 저장하지 않습니다.

## 기술 스택

- Python 3.12, [uv](https://docs.astral.sh/uv/) (패키지 관리)
- Streamlit (웹 화면)
- OpenCV, NumPy (영상 처리)
- Firebase Authentication, Cloud Firestore (로그인, 데이터 저장)
- pytest (테스트)
- JCloud Ubuntu 서버 + systemd (배포)

## 폴더 구조

```
app.py            메인 화면
pages/            추가 화면 (Streamlit 멀티 페이지)
modules/          로그인, 권한, 케이스 저장·검색, 상태 변경, ROI
algorithms/       필터, CLAHE, Canny, Otsu, 화질 지표
tests/            pytest 테스트
```

## 로컬 실행 (Windows PowerShell)

1. uv 설치 (처음 한 번)
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. 레포 받기
   ```
   git clone https://github.com/leeseojoon5793/choboproject.git
   cd choboproject
   ```
3. 패키지 설치와 실행
   ```
   uv sync
   uv run streamlit run app.py
   ```

`.streamlit/secrets.toml`이 없으면 **가짜 로그인 모드**로 실행됩니다. 사이드바에서 역할을 골라 로그인하고, 데이터는 `data/` 폴더의 JSON 파일에 저장됩니다. Firebase 없이 화면과 기능을 확인할 때 사용합니다.

## Firebase 연결

Firebase 로그인과 Firestore를 쓰려면 `.streamlit/secrets.toml`을 만듭니다.

```toml
firebase_api_key = "Firebase 웹 API 키"
service_account_path = "서비스 계정 키 JSON 파일 경로"
data_dir = "업로드 영상을 저장할 폴더 (생략하면 data/)"
```

- `secrets.toml`과 서비스 계정 키 파일은 **절대 커밋하지 않습니다.** `secrets.toml`은 `.gitignore`에 포함되어 있고, 키 파일은 레포 폴더 밖에 둡니다.
- 키와 테스트 계정 정보는 팀 내부로만 공유합니다.

### Firestore 컬렉션

| 컬렉션 | 내용 |
|---|---|
| `users` | 문서 ID = uid, 이메일, 역할 |
| `cases` | 케이스 정보, 상태, 등록자, 검토 담당, 영상 폴더 경로 |
| `images` | 슬라이스별 파일 경로(상대 경로), 슬라이스 번호 |
| `process_logs` | 알고리즘, 파라미터, ROI, 결과 경로, 지표 |
| `memos` | 검토 메모·소견 (수정 없이 추가만) |
| `status_logs` | 상태 변경 이력 (이전 상태, 다음 상태, 변경자, 사유) |

시간은 UTC `YYYY-MM-DDTHH:MM:SSZ` 형식, 파일 경로는 `data_dir` 기준 상대 경로로 저장합니다.

## 역할과 상태 변경 권한

| 변경 | 할 수 있는 역할 |
|---|---|
| 접수 → 배정 | 관리 담당 (검토 담당 지정 필수) |
| 배정 → 검토 중 | 배정된 검토 담당 |
| 검토 중 → 완료 | 배정된 검토 담당 |
| 검토 중 → 재검토 요청 | 배정된 검토 담당 (사유 필수) |
| 재검토 요청 → 접수 | 등록한 등록 담당 |
| 완료 → 검토 중 | 관리 담당 |

조회는 등록 담당은 본인이 등록한 케이스만, 검토 담당과 관리 담당은 전체 케이스를 볼 수 있습니다.

## 테스트

```
uv run pytest
```

## 서버 배포

JCloud Ubuntu 인스턴스에서 systemd 서비스(`choboproject`)로 Streamlit을 8080 포트에 실행합니다. develop 브랜치가 반영되어 있습니다.

develop에 새 PR이 머지되면 서버에서 아래 명령으로 반영합니다.

```
cd ~/choboproject
git pull
uv sync
sudo systemctl restart choboproject
```

상태 확인과 로그:

```
sudo systemctl status choboproject --no-pager
journalctl -u choboproject -n 50 --no-pager
```

## 협업 규칙

- 브랜치: Gitflow (`main` / `develop` / `feature/*`). `main`과 `develop`에 직접 커밋하지 않습니다.
- 작업 순서: Issue 생성 → `feature/*` 브랜치 → PR(develop 대상) → 리뷰어 Approve → PR 작성자가 머지 → 브랜치 삭제
- 커밋 메시지: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore` + 한 줄 설명 + Issue 번호
  예) `feat: 역할별 케이스 상태 변경 화면 추가 (#30)`

## 팀원과 역할

| 역할 | 담당 | 팀원 |
|---|---|---|
| A | 인증·권한·배포, 팀장 | 이서준 |
| B | 케이스 등록·저장·검색 | 김초원 |
| C | 영상 처리 알고리즘·ROI·화질 지표·뷰어 화면 | 배해인 |
| D | 케이스 목록·알고리즘 추천 화면 | 백보명 |