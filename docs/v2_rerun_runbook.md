# v2 재실험 실행 순서 (greedy acceptance 최종 엔진)

JKIIE 심사 대비 수정으로 최종 VAA-GILS에서 SA acceptance와 reheating을 제거했다
(greedy acceptance + best-improvement descent + kick restart). 논문의 GILS 관련 수치는
모두 SA 엔진으로 얻은 값이라 다시 측정해야 하며, 그전까지 `paper/jkiie_submit_body.tex`에는
`[TBD]`가 남아 있다. 이 문서는 Mac(Apple M2)에서 재실험을 돌리는 순서를 정리한다.

## 사전 확인

- Windows에서 수정한 코드가 Mac 저장소에 반영되어 있어야 한다(아직 커밋 전).
- 새 엔진 메서드는 `v2-GILS-...` 이름을 쓴다. 러너는 이미 기록된 작업을 건너뛰므로
  기존 CP-SAT, VAA, Paper-SA-RL5 결과는 그대로 재사용되고 CP-SAT는 다시 돌지 않는다.
- 예전 SA 엔진 기록(`GILS-...`)은 결과 파일에 남지만 요약 스크립트가 무시한다.
- 긴 단계는 끊겨도 같은 명령을 다시 실행하면 남은 작업만 이어서 돈다
  (5단계 λ 탐색은 예외: 처음부터 다시 돌고 파일을 덮어쓴다).

## 0. 코드 점검 (권장, 수 분)

```
pytest
```

실험을 몇 시간 돌리기 전에 코드 오류를 먼저 잡기 위한 단계다. 7단계에서 한 번 더 돌린다.

## 1. acceptance 규칙 확인 — 판단 게이트

```
python experiments/acceptance_tuning.py
```

- 조정 집합(tuning pool), 9개 조건 × 인스턴스 5개 × 반복 5회 × 2개 방법 = 450회
- 결과: `outputs/acceptance_tuning.jsonl`, 마지막에 요약이 출력된다
- 읽는 법: `mean`이 양수면 SA가 greedy보다 나쁘다는 뜻이다

**여기서 멈추고 판단한다.** SA가 greedy보다 유의하게 좋게 나오면(mean < 0, p < 0.05)
SA 제거 결정 자체를 다시 검토해야 하므로 2단계 이후를 진행하지 않는다.
출력(all / none / TW 세 줄)은 논문 4장 acceptance 문장의 `[TBD]`에 쓴다.

## 2. DQN 재학습

```
cp outputs/models/gvaa_dqn.pt outputs/models/gvaa_dqn_sa_engine.pt
python experiments/train_gvaa.py --episodes 500
```

- 기존 체크포인트는 SA 엔진으로 학습되어 덮어쓰기 전에 백업한다
- `--episodes 500`을 반드시 준다. 스크립트 기본값은 300이지만 부록 A와 기존 체크포인트는 500회다
- `v2-GILS-dqn-*` 메서드가 이 체크포인트를 읽으므로 3단계보다 먼저 끝나야 한다

## 3. 주 실험 (Table 3, Table 6, Figure 1)

```
python experiments/k1_run.py search
python experiments/k1_run.py budget
```

- `search`: 새 작업 3,300회
  - v2-GILS(uniform/tabular/DQN) 9개 조건 × 20개 인스턴스 × 5회 = 2,700회
  - Extended-SA-RL5 medium·tight 6개 조건 × 20개 × 5회 = 600회
- `budget`: 9개 조건 × 5개 × 반복 횟수 3종 × 선택 정책 3종 × 5회 = 2,025회
- 결과: `outputs/k1_results.jsonl`에 이어서 기록

## 4. ablation (Table 4, Table 5, Figure 2, Figure 3)

```
python experiments/b1_run.py
python experiments/b2_run.py
```

- `b1`: 연산자 집합 3종, 9 × 5 × 3 × 5 = 675회 → `outputs/b1_guided_ablation.jsonl`
- `b2`: 최종 엔진 기준 한 가지씩 변경(기준 / descent 제거 / restart 제거 /
  무작위 초기해 / SA 추가) 9 × 5 × 5 × 5 = 1,125회 → `outputs/b2_component_ablation.jsonl`

## 5. λ 민감도 (6.4절, Figure 4)

```
python experiments/lambda_sensitivity.py
python experiments/lambda_summary.py
```

- 최종 엔진(균등 선택 + greedy)으로 조정 집합에서 3 × 2 × 5 × 3 × 7 = 630회
- `outputs/lambda_sensitivity.jsonl`을 덮어쓰고 `outputs/lambda_curve.json`을 만든다

## 6. 요약

```
python experiments/k1_stats.py   > outputs/k1_stats.txt
python experiments/k1_summary.py > outputs/k1_summary.txt
python experiments/b1_summary.py > outputs/b1_summary.txt
python experiments/b2_summary.py > outputs/b2_summary.txt
```

`k1_stats.txt`에는 GILS-uniform 대 VAA, Paper-SA-RL5(none), Extended-SA-RL5(medium·tight)
비교가 들어 있다. 6.1절의 VAA 2.65% / SA-RL5 1.38% 불일치도 이 결과로 정리한다.

## 7. 최종 테스트

```
pytest
```

## 실행 후 할 일

결과 파일(`outputs/*.txt`, `outputs/acceptance_tuning.jsonl`, `outputs/lambda_curve.json`)을
가져오면 다음을 채운다.

1. `paper/jkiie_submit_body.tex`의 `[TBD]`와 `% TODO` 주석
   - 초록, 4장 acceptance 문장, 6.1절 문단, Table 3–6, 6.2절 Engine components 서술,
     6.4절 수치, 7장, 결론
   - 6.2절 단조 감소, 6.3절 균등 선택 우위 같은 정성적 서술이 여전히 성립하는지 확인
2. `experiments/make_figures.py`의 Figure 1–3 수치가 코드에 직접 들어 있으므로 새 결과로 교체
   (Figure 3의 "Stochastic acceptance" 막대는 "Add SA acceptance + reheating"으로 변경)
3. `paper/jkiie_submit_body.docx`, `paper/jkiie_submit_titlepage.docx` 갱신
   (제목 변경, Table 3 Extended-SA-RL5 행 추가, Table 6 n 열 추가 포함)
