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

사용자가 입력한 기사는 System Orchestrator를 통해 두 경로로 처리됩니다. 한 경로에서는 불필요한 정보 제거와 토큰화를 거쳐 광고성·자극성·낚시성 검증 모델로 기사 유형을 판별하고, 다른 경로에서는 키워드 추출·벡터 생성과 MeSH 영문 매핑 후 FAISS 검색으로 유사 문서를 찾아 PubMed 문서를 조회하고 RAG로 사실 여부를 확인합니다. 두 결과를 다시 통합한 뒤 Gemini 3 Pro가 최종적으로 신뢰 기사, 광고·낚시·자극적인 기3.1 KPF-BERT 데이터셋 준비와 Fine-tuning
  KPF-BERT모델은 뉴스 기사 특유의 문체와 전문 용어를 통해서만 가짜뉴스를 판단한다. 따라서 문맥을 통해서 가짜뉴스의 이해할 수 있도록 Fine-tuning시킬 데이터 확보가 필요하다. 먼저 낚시성 기사는 한국지능정보사회진흥원이 운영하는 AI Hub에서 공개한 ‘낚시성 기사 탐지 데이터셋’을 활용한다[11]. 광고성·자극성 기사는 인터넷 신문 윤리위원회의 기사 심의 결정문 속 PDF를 크롤링해 준비한다. 해당 문서는 2020년부터 2026년까지의 정보를 수집하며 어떤 조항을 위반했는지 명시되어있다. 정상 기사는 한국언론진흥재단의 뉴스토어에서 구매한 국민일보, 중앙일보, 한겨례에 API를 사용해 URL 제거, 제목과 본문 길이가 짧은 기사를 제외하고 수집한다.
  본 연구는 Fine-tuning을 위해서 선행 연구의 방식을 따른다[9]. KPF-BERT 모델에 Linear Layer를 추가하여 분류 작업을 할 수 있도록 설정한다. 이후 출력은 Softmax를 거쳐 확률값으로 변환되고 학습에는 CrossEntropyLoss를 손실함수로, AdamW를 활성화 함수로 사용한다.

3.2. System Orchestrator
  System Orchestrator는 두 모델을 관리하고 작업을 적절히 할당하며, 각각의 결과를 종합해 출력하는 소프트웨어이다. 이는 Data Integrator 역할을 수행한다. 먼저 검증할 뉴스를 입력받아 KPF-BERT와 CRAG를 동시에 전달한다. 두 모듈은 작업을 끝낼 때까지 기다리는 비동기 처리를 하고, 이후 BERT가 내놓은 점수와 CRAG가 찾아온 참조 문장을 정리해 Gemini에게 보낸다.
 
3.3 KPF-BERT 단계
  기사 내 문체적 특징과 형식적 패턴을 분석한다. 입력 데이터는 전처리 및 토큰화를 거쳐 KPF-BERT에 입력되며, 모델은 어휘 사용, 문체 등의 언어적 특징을 기반으로 뉴스의 신뢰도 점수를 산출한다.사, 근거 있는 가짜 뉴스 등으로 분류하여 **최종 판별 결과**를 산출합니다.

3.3 KPF-BERT 단계
  기사 내 문체적 특징과 형식적 패턴을 분석한다. 입력 데이터는 전처리 및 토큰화를 거쳐 KPF-BERT에 입력되며, 모델은 어휘 사용, 문체 등의 언어적 특징을 기반으로 뉴스의 신뢰도 점수를 산출한다. 

3.4 RAG 단계
  기존의 CRAG의 형태를 참고해 RAG단계를 진행한다.[12] 차이점은 CRAG는 한 개의 언어만을 지원하지만 한국어로 입력된 기사가 영어단어와 매핑되어 영어DB에서 검색된다. 기존의 모델은 먼저 한국어 기사 본문에서 핵심 키워드를 추출하여 영어 의학 용어로 변환 및 쿼리를 생성한다. 이후 PubMed API를 통해 관련 논문을 수집된 글로벌 DB에서 검색한다. Retrieval Evaluator를 통해 수집된 문서가 낚시성 기사와 광고성·자극성 기사와 실제로 관련이 있는지 Confidence Degree를 매긴다. 검색 결과가 적절할 경우, 원문에서 질문과 관련된 문장만 요약하여 노이즈를 제거한다. 검색 결과가 부적절할 경우 Google News API를 통해 추가 정보를 확보한다.
