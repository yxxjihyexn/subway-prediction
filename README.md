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

## 주요 기능
- 예측하기: 연도/월/호선/역/시간대 선택 → 예상 승차 인원 예측
- 기록 조회: 예측 이력 확인 (MongoDB 저장)
- 인사이트: 시간대별/역별 승하차 데이터 시각화

## 모델 성능
- MAE: (숫자)
- RMSE: (숫자)
- R2: (숫자)

## 화면 미리보기

### 예측 화면
![예측 화면](image/예측%20화면_default.png예측_화면_default.png)
![예측 결과](image/예측%20화면_after.png예측_화면_after.png)

### 기록 조회 화면
![기록 조회](image/기록%20조회%20화면.png기록_조회_화면.png)
![기록 조회 - 빈 상태](image/기록%20조회%20화면_empty.png기록_조회_화면_empty.png)

### 인사이트 화면
![인사이트](image/인사이트%20화면.png인사이트_화면.png)