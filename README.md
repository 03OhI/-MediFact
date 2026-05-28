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
```

<img width="716" height="337" alt="화면 캡처 2026-05-28 152115" src="https://github.com/user-attachments/assets/86681479-268c-4086-b870-512cda264faa" />

> **MediFact 시스템 아키텍처** — 데이터 구축부터 모델 학습, 실시간 추론까지의 전체 파이프라인을 세 단계로 나타낸 흐름도입니다.

위 그림은 MediFact의 동작 과정을 **① 데이터 준비 및 전처리 → ② KPF-BERT 파인튜닝 → ③ 추론 및 검증 로직**의 세 단계로 구성하여 보여줍니다.

**① 데이터 준비 및 전처리**

두 갈래로 데이터를 구축합니다. 한쪽은 *KPF-BERT 파인튜닝용 학습 데이터셋*으로, 인터넷 신문윤리위원회 심의문·AI Hub·뉴스토어 API에서 기사를 수집한 뒤 텍스트 전처리와 형태소 분석을 거쳐 광고성·자극성·낚시성 기사로 분류합니다. 이후 데이터 정제 조건 검증(불용어 처리 및 재검증)과 데이터 균형 조절을 거쳐 JSON 구조로 변환·저장하고, Train/Valid/Test로 분리해 학습용 데이터셋을 완성합니다. 다른 한쪽은 *RAG(CRAG) 모듈용 의학 논문 벡터 DB*로, MeSH 의학용어 한/영 매핑 사전을 구축하고 PubMed API로 논문 초록과 메타데이터를 수집한 뒤 BioBERT로 임베딩하여 FAISS 벡터 데이터베이스를 구축합니다.

**② KPF-BERT 파인튜닝 과정**

전처리된 데이터를 `[CLS]제목[SEP]본문[SEP]` 형태로 입력받아 임베딩 및 학습을 진행합니다. 마지막 은닉층에 Linear Layer를 추가하고 AdamW 최적화와 CrossEntropyLoss 손실 함수를 사용하며, softmax로 확률값을 산출합니다. 학습이 완료되면 Precision·Recall·F1-score로 성능을 평가하여 낚시성·자극성·광고성 검증 모델을 각각 생성합니다.

**③ 추론 및 검증 로직**

사용자가 입력한 기사는 System Orchestrator를 통해 두 경로로 처리됩니다. 한 경로에서는 불필요한 정보 제거와 토큰화를 거쳐 광고성·자극성·낚시성 검증 모델로 기사 유형을 판별하고, 다른 경로에서는 키워드 추출·벡터 생성과 MeSH 영문 매핑 후 FAISS 검색으로 유사 문서를 찾아 PubMed 문서를 조회하고 RAG로 사실 여부를 확인합니다. 두 결과를 다시 통합한 뒤 Gemini 3 Pro가 최종적으로 신뢰 기사, 광고·낚시·자극적인 기사, 근거 있는 가짜 뉴스 등으로 분류하여 **최종 판별 결과**를 산출합니다.
