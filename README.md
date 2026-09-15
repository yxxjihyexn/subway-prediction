# 지하철 이용객 수 예측

## 프로젝트 소개
서울시 지하철 시간대별 승하차 데이터를 활용해, 연도/월/호선/역/시간대 조건에 따른
예상 승차 인원을 예측하는 머신러닝 웹 서비스입니다.

## 사용 기술
- 데이터: 서울 열린데이터광장 - 지하철 시간대별 승하차 인원
- 머신러닝: scikit-learn (RandomForestRegressor)
- 웹: Streamlit
- 데이터베이스: MongoDB
- 화면 설계: Figma
- AI 협업: Claude (Anthropic) — 코드 작성 가이드, 디버깅, 문서화 지원

## 폴더 구조
├── data/subway.csv
├── model/ (학습된 모델, 인코더, 옵션 목록)
├── ml_project_subway.ipynb (데이터 분석 및 모델 학습)
├── app.py (Streamlit 웹 앱)
└── requirements.txt

## 실행 방법
1. pip install -r requirements.txt
2. MongoDB 로컬 실행
3. streamlit run app.py

## MongoDB 연동

- **Database**: `subway_prediction`
- **Collection**: `predictions`

예측하기 화면에서 "예측하기" 버튼을 누를 때마다, 아래 형태로 문서 하나가 저장됩니다.

```json
{
  "연도": 2026,
  "월": 10,
  "호선명": "2호선",
  "지하철역": "신림",
  "시간대": "17시-18시",
  "예측인원": 66869,
  "예측시각": "2026-09-14T15:52:00"
}
```

| 필드 | 설명 |
|---|---|
| 연도, 월, 호선명, 지하철역, 시간대 | 사용자가 선택한 예측 조건 |
| 예측인원 | 모델이 예측한 승차 인원 |
| 예측시각 | 예측을 실행한 시각 |

기록 조회 화면에서는 `예측시각` 기준 내림차순으로 정렬해, 가장 최근 예측 20건을 조회해 보여줍니다.

## 주요 기능
- 예측하기: 연도/월/호선/역/시간대 선택 → 예상 승차 인원 예측
- 기록 조회: 예측 이력 확인 (MongoDB 저장)
- 인사이트: 시간대별/역별 승하차 데이터 시각화

## 모델 성능
- MAE: 8,345
- RMSE: 13,581
- R2: 0.632

## 화면 미리보기

### 예측 화면
![예측 화면](image/예측%20화면_default.png)
![예측 결과](image/prediction.png)

### 기록 조회 화면
![기록 조회](image/recording.png)
![기록 조회 - 빈 상태](image/기록%20조회%20화면_empty.png)

### 인사이트 화면
![인사이트](image/insight.png)