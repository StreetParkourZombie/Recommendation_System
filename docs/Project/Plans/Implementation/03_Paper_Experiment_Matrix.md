# Paper-to-Experiment Matrix

| Paper | Claim used | Project experiment | Metric/evidence | Reproduction or project run |
|---|---|---|---|---|
| 01 | Temporal leakage can alter offline model comparison | Compare random, global temporal, leave-one-out; diagnose future-in-train vs test | split counts, leakage rate, ranking metrics | Paper 01 reproduction + project run |
| 02 | Evaluation strategy contributes to popularity-bias divergence | Hold data/model/grouping fixed while comparing split | popularity metrics, `%DeltaGAP` only if protocol matched | Paper 02 reproduction + project run |
| 03 | Split strategy changes sequential evaluation | Compare project split definitions; optional sequential repository | ranking metrics and rank stability | method-informed unless exact setup matched |
| 04 | Sparse offline ranking may diverge from dense judgment ranking | Discuss validity limitation; no dense claim without data | correlation only if dense data obtained | literature support |
| 05-10 | Bias, cold-start and evaluation validity need explicit definitions | Define terminology, limitations and future work | cited definitions; not direct quantitative evidence | literature support |
| 11 | Metric implementation details change outcomes | Unit-test metric contract | hand-computed fixtures and consistency checks | implementation control |
| 12 | Split strategy is an evaluation design choice | Compare split definitions and prior findings | metric/ranking sensitivity | literature-informed project run |
| 13-14 | Big Data execution and evaluation need environment disclosure | Run Spark local/Colab simulation and record runtime | hardware manifest, runtime, scale notes | architecture reference |

## Rule

One row does not prove paper reproduction. Reproduction requires matching paper protocol and artifact evidence. Project run answers project RQ under frozen protocol.
