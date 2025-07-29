# 다중 지표 × 다중 타임프레임 전략 시스템 설계서

## 1. 개요
본 문서는 Binance 선물 시장을 대상으로 10배 레버리지의 1~2시간 스윙(단타) 포지션을 주로 운용하기 위한 "다중 지표 × 다중 타임프레임" 자동매매 시스템의 설계 방향을 정의한다. 핵심 목표는 과최적화를 방지하면서도 각 지표·타임프레임 조합의 실제 성공 확률이 80% 이상인 경우에만 진입하도록 확률 기반 의사결정 체계를 구축하는 것이다.

## 2. 시스템 아키텍처 개요
```mermaid
flowchart TD
  subgraph 데이터레이어
    A[Binance Futures API] --> B[실시간 & 과거 OHLCV 수집]
    B --> C[데이터 레이크 (Parquet / Time-Series DB)]
  end

  subgraph 리서치/백테스트 파이프라인
    C --> D1[지표 파라미터 최적화]
    D1 --> D2[백테스트 & 성능평가]
    D2 --> D3[가중치·임계치 산정]
  end

  subgraph 프로덕션 엔진
    D3 --> E[실시간 시그널 계산]
    E --> F[확률 캘리브레이션]
    F --> G{진입 조건 P ≥ 0.8?}
    G -- Yes --> H[주문 실행 / 포지션 관리]
    G -- No --> I[관망]
  end
```

### 2.1 주요 모듈
1. **데이터 수집기**: REST/WebSocket 혼합·자동 리샘플링(5m·15m·1h·4h·1d)
2. **지표 엔진**: TA-Lib + 커스텀 구현(RSI, Supertrend, Bollinger, CCI, MACD 등)
3. **파라미터 최적화기**: Bayesian Optimization(Optuna)·PSO·Grid Search 지원
4. **백테스트 프레임워크**: Backtrader 커스텀(10배 레버리지, 슬리피지·수수료 반영)
5. **성능 평가기**: 승률·Profit Factor·Information Coefficient·Sharpe·MaxDD
6. **가중치 계산기**: SHAP / Permutation Importance + 분산 민감도 → 정규화
7. **확률 캘리브레이터**: 로지스틱 회귀·Platt Scaling·Isotonic Regression
8. **멀티 타임프레임 애그리게이터**: 각 TF별 점수 → 계층적 가중 합산
9. **리스크·포지션 관리**: 고정 10x 레버리지, 0.5% SL, 변동성 기반 TP
10. **실시간 주문 라우터**: Binance API 제한·에러 핸들링 내장
11. **거래비용·유동성 모델러**: 오더북 Depth 기반 슬리피지·마켓임팩트 함수, 펀딩비 시뮬레이터
12. **리스크 가드**: 포지션 캡·ADL(자동디레버리지) 모니터·Circuit Breaker·Latency 모니터링
13. **Order-Book Replay 엔진**: 실시간 지연·체결율 시뮬레이션으로 백테스트-실거래 차단간 검증
14. **대시보드/알림 서비스**: Prometheus/Grafana + Telegram/Slack 알림, 이상치 탐지 이벤트

## 3. 데이터 설계
| 항목 | 내용 |
|------|------|
| 소스 | Binance USDT-M Futures 모든 코인 |
| 필터 | 24h 거래대금 상위 50종목(기본) |
| 타임프레임 | 5m, 15m, 1h, 4h, 1d |
| 보존 정책 | 원본 그대로 S3/MinIO‧Parquet + DuckDB 뷰 |
| Depth/Funding | 20호가 오더북, 펀딩비 히스토리 수집·저장 |

## 4. 지표 및 파라미터 공간
| 지표 | 기본 파라미터 공간 | 최적화 기법 |
|------|------------------|-------------|
| RSI | period 2-6, overbought 70-90, oversold 10-40 | Grid + Bayesian |
| Supertrend | ATR period 7-21, multiplier 1-5 | Bayesian |
| Bollinger | period 14-50, std 1.5-3.0 | PSO |
| CCI | period 10-40 | PSO |
| MACD | fast 8-12, slow 20-30, signal 5-12 | Grid |
| Risk Params (SL/RR) | SL 0.3-1.0%, RR 1.2-3.0 | Grid |

## 5. 파라미터 최적화 로직
1. **객체 함수**: Sharpe × (1 ‑ MaxDD) 혹은 custom utility
2. **리스크 파라미터 탐색**: SL, RR(Reward-Risk) 값을 동일 실험 내 Grid/Bayesian 최적화에 포함
3. **Cross-Validation**: Time-Series K-Fold + Walk-Forward
4. **Early Stopping**: 3회 연속 성과 하락 시 탐색 중단

## 6. 성능지표 및 가중치 산정
1. **성과 벡터**: WinRate, PF, IC → Min-Max 정규화 후 합산
2. **Feature Importance**: 모델(XGB) → SHAP 평균 절대값
3. **분산 기반 민감도**: Sobol 지수
4. **최종 가중치**: 위 세 항목 평균 후 전체 합으로 나눠 정규화
5. **타임프레임 가중치 최적화**: Optuna Trial에 TF 가중치(continuous, Σ=1)를 포함하여 공동 최적화

## 7. 확률 기반 임계치 설정
1. 백테스트 시그널 → 로지스틱 회귀로 `P(익절|score)` 추정
2. ROC → Youden’s J 최대 지점의 P* 도출(기본 0.8)
3. 실시간에서는 P ≥ P*이면 진입, 아니면 패스

## 8. 멀티 타임프레임 융합 규칙
1. 상위 TF(1d,4h) → 시장 방향 필터
2. 중간 TF(1h) → 포지션 방향 확정
3. 하위 TF(15m,5m) → 트리거·정교한 진입 타이밍
4. 각 층별 가중치를 별도 학습 또는 휴리스틱(예: 0.4/0.3/0.3)

## 9. 리스크 관리 및 거래 규칙
* 고정 레버리지 10x, **포지션 사이징: 풀시드(계좌 잔고 100%)**
* 손절(SL): 0.3%~1.0% 범위, 최적화 대상
* 이익실현(TP): RR 1.2~3.0 범위, 최적화 대상 (예: RR=1.8 → TP=SL×1.8)
* 슬리피지: 0 (가정), **수수료: 왕복 0.5 %**를 모든 백테스트·실거래 계산에 포함
* ADL 위험·유지 증거금 체크, 주문량 캡, Circuit Breaker(연속 3실패 시 중단)
* 펀딩비·수수료 변동 반영 후 기대값<0이면 진입 취소 혹은 디레버리지
* 이상치 캔들·Fake 무빙 필터: 체결 수 ⩽ N, OHLC 고저폭 > Xσ → 시그널 무효화

## 10. 기술 스택 & 인프라
| 레이어 | 기술 |
|--------|------|
| 언어 | Python 3.10 |
| 데이터 | pandas, numpy, DuckDB, Parquet |
| 지표 | TA-Lib, pandas-ta |
| 최적화 | Optuna, pyswarms |
| ML/통계 | scikit-learn, XGBoost, shap |
| 백테스트 | Backtrader, vectorbt (실험적) |
| MLOps | MLflow, Optuna-dashboard |
| 배포 | Docker, GitHub Actions, Prometheus + Grafana |
| 보안 | AWS KMS, HashiCorp Vault, 2FA, IP Whitelist |

## 11. 검증 전략
1. In-sample / Out-of-sample 분리
2. Walk-forward 6개월 윈도, 한 달 스텝
3. 슬리피지·수수료·펀딩비 모두 포함
4. Reality Check: White’s Reality Check로 데이터 마이닝 편향 보정
5. Order-Book Replay 테스트: 실시간 오더북 재생으로 지연·체결율 차이 분석
6. Latency Drift 모니터링: 평균 API Round-Trip > X ms 시 시그널 무효화

## 12. 보안 & 운영 고려사항
* API Key 암호화(.env + AWS KMS)
* 주문 한도 체크 및 비상 스위치
* 실시간 모니터링 알림(Telegram/Slack)

## 13. 향후 로드맵
* 강화학습 기반 포지션 사이징 모듈
* 옵션·스팟 시장 확장
* AutoML로 지표 자동 선택 
* Paper Trading → Live 단계별 전환 시나리오
* 규제·컴플라이언스 체크리스트(GPL/LGPL, 암호화폐 파생 규제)
* 실시간 대시보드(지표 히트맵·PnL·Latency) 고도화 