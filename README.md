# -MediFact
졸업작품 메디팩트 

## 🛠️ 환경 설정

### 요구 사항

- **Python 3.12** (Conda 환경 권장)
- **Conda** (Miniconda 또는 Anaconda)
- **Google Gemini API 키** (LLM 통합용)
- GPU는 선택 사항이지만, BERT 계열 모델 파인튜닝 시 권장됩니다.

### 설치

저장소를 클론한 뒤 `environment.yml`로 Conda 환경을 생성합니다.

```bash
git clone <repository-url>
cd medifact

# Conda 환경 생성 및 활성화
conda env create -f environment.yml
conda activate medifact
```

### 추가 설정

일부 라이브러리는 환경 생성 후 별도 리소스 다운로드가 필요합니다.

```bash
# spaCy 영어 모델 (pytextrank 연동에 필요)
python -m spacy download en_core_web_sm
```

Gemini API 키는 환경 변수로 설정합니다.

```bash
export GOOGLE_API_KEY="your-api-key-here"   # Windows: set GOOGLE_API_KEY=...
```<img width="716" height="337" alt="화면 캡처 2026-05-28 152115" src="https://github.com/user-attachments/assets/254ede57-6edd-4346-a853-e908d36b127b" />


<img width="716" height="337" alt="화면 캡처 2026-05-28 152115" src="https://github.com/user-attachments/assets/e1a3c926-7a6b-4c69-addb-f9c93c988519" />
