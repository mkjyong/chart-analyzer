# 개발 계획서 (plan.md)

## 0. 개요
본 계획서는 "다중 지표 × 다중 타임프레임" 전략 시스템을 7주 이내에 MVP 수준으로 구현하기 위한 단계별 로드맵을 제시한다. 기간·인력은 1인 개발 기준으로 산정하였다.

---

## 1. 일정 개요 (Gantt 요약)
| 주차 | 주요 마일스톤 |
|------|---------------|
| 1주차 | 환경 구축 & 데이터 수집 모듈 완성 |
| 2주차 | 지표 엔진 + 첫 번째 파라미터 최적화 PoC |
| 3주차 | 백테스트 엔진(Core) & Optuna 통합 |
| 4주차 | SHAP 기반 가중치 계산 + 로지스틱 캘리브레이션 |
| 5주차 | 멀티 타임프레임 애그리게이터 구현 |
| 6주차 | 종합 전략 Walk-Forward 백테스트 & 리포트 |
| 7주차 | Docker 배포, 문서화, 코드 리팩터, CI/CD |
| 8주차 | Paper Trading(실시간 데이터·모의주문) & 리스크 가드 튜닝 |
| 9주차 | Live Deployment + 대시보드/알림 고도화 & 운영 안정화 |

---

## 2. 세부 작업 항목
### 1주차 – 환경 & 데이터 레이어
1. Python 3.10 가상환경 + `requirements.txt` 작성
2. `python-binance` (또는 CCXT)로 USDT-M 선물 OHLCV 수집 스크립트 작성
3. 5m~1d 리샘플 · Parquet 저장 · DuckDB 뷰 생성
4. 기본 데이터 검증(결측·이상치 처리)

### 2주차 – 지표 엔진 & 파라미터 최적화 PoC
1. TA-Lib 래퍼 클래스 설계(멀티 타임프레임 지원)
2. RSI(Period 2-6) + Supertrend(ATR) 두 지표로 최소한의 전략 정의
3. Optuna를 이용해 파라미터 최적화 PoC 실행
4. 노트북으로 시각화 및 리포트 작성

### 3주차 – 백테스트 엔진 & 최적화 프레임워크
1. Backtrader Fork → 레버리지·수수료·펀딩비 커스텀
2. Optuna / pyswarms 공통 인터페이스 작성
3. Objective: Sharpe × (1-MaxDD) 함수 구현
4. TimeSeriesSplit Walk-Forward 적용
5. SL/RR(0.3-1.0%, 1.2-3.0) 그리드/베이지안 탐색 통합

### 4주차 – 성능 평가 & 가중치 계산
1. Backtest 결과 → WinRate, PF, IC 추출
2. XGBoost 모델로 SHAP 값 계산
3. Sobol 민감도 분석 스크립트 작성
4. 가중치 정규화 로직 구현 및 단위 테스트
5. 로지스틱 회귀로 확률 캘리브레이션

### 5주차 – 멀티 타임프레임 애그리게이터
1. 상·중·하위 TF 계층 구조 클래스 설계
2. 각 TF별 점수 → 최종 Score 산출 로직 구현
3. 실시간 시그널 시뮬레이션(Replay) 테스트

### 6주차 – 종합 백테스트 & 검증
1. 최근 2년 데이터 Walk-Forward 전 구간 실행
2. White’s Reality Check, Bootstrapping으로 통계적 유의성 검증
3. 결과 리포트 자동 생성을 위한 Jupyter-Book 템플릿 작성

### 7주차 – 배포 · 문서화 · 자동화 (CI/CD & MLOps)
1. MLflow 실험 저장소 세팅, Optuna-dashboard 연결
2. Dockerfile, docker-compose 작성 및 CI 파이프라인 강화
3. 보안: Vault로 API 키 관리, 2FA·IP 화이트리스트 설정

### 8주차 – Paper Trading & 리스크 가드
1. 실시간 데이터 스트림 + 모의 주문 시스템 구축
2. Order-Book Replay 모드로 Latency Drift 검증
3. Circuit Breaker, 포지션 캡, ADL 모니터 실전 튜닝

### 9주차 – Live 운영 & 대시보드 고도화
1. 실계좌 Live 배포, 초기 제한 모드(포지션 크기 10% 풀시드)
2. Grafana 대시보드: PnL, Latency, 슬리피지, 지표 Heatmap
3. 스케일 아웃(멀티 인스턴스) 및 운영 문서 완성

---

## 3. 리스크 관리 및 완화 플랜
| 리스크 | 영향 | 대응 |
|--------|------|------|
| Binance API 제한 | 데이터 수집 지연 | WebSocket 병행, 백오프 로직 |
| 과최적화 | 실계좌 손실 | Walk-Forward + Reality Check, drop worst models |
| 수수료·비용 과소평가 | 수익 악화 | 백테스트에 왕복 0.5% 수수료, 슬리피지 0 적용 반영 |
| Latency Drift | 체결 불일치 | Order-Book Replay, API RTT 모니터링 & 알람 |
| 규제/라이선스 이슈 | 서비스 중단 위험 | GPL/LGPL 및 암호화폐 파衍 규제 사전 검토 |

---

## 4. 완료 기준(Definition of Done)
1. design.md·plan.md·README 완비 및 최신화
2. end-to-end 백테스트에서 CAGR, Sharpe, MaxDD 리포트 자동 생성
3. Docker 이미지 한 번의 명령으로 시그널 생성까지 동작
4. GitHub Actions 자동 배포 성공
5. 핵심 로직(지표·백테스터·가중치) 단위 테스트 커버리지 ≥80%
6. Paper Trading 2주 이상 무사고 기록
7. MLflow/Optuna 실험 및 모델 버전 태깅, 재현 가능

---

## 5. 향후 과제
* 강화학습 기반 포지션 사이징
* 멀티자산(옵션, 스팟) 확장
* 실시간 슬리피지/시장충격 모델 개선 