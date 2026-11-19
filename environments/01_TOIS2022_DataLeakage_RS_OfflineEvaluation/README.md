# Paper 01 reproduction environment

This environment targets BPR and NeuMF from dataLeakageRec.

## Build

```powershell
docker build -t paper01-tf114 .
```

Run from repository root:

```powershell
docker run --rm -it `
  -v "${PWD}\docs\References\Papers\Code\dataLeakageRec:/workspace/dataLeakageRec" `
  -v "${PWD}\datasets:/workspace/datasets" `
  -v "${PWD}\reproduction_runs\paper01:/workspace/reproduction_runs" `
  paper01-tf114 bash
```

Inside container:

```bash
python -c "import tensorflow as tf, keras, numpy, scipy; print(tf.__version__, keras.__version__, numpy.__version__, scipy.__version__)"
```

Verified image:

```text
paper01-tf114:latest
Python 3.6.x
TensorFlow 1.14.0
Keras 2.3.0
NumPy 1.18.5
SciPy 1.4.1
h5py 2.10.0
```

The paper does not report hardware, operating system, exact software versions, or exact seed values. Record local host and Docker image details for every run.

Check mounts before training:

```bash
ls -lh /workspace/datasets/movielens
ls -lh /workspace/dataLeakageRec/BPR
```

Expected MovieLens files:

```text
data.data.RATING
test.test.RATING
test.train.RATING
train.test.RATING
train.train.RATING
```



## BPR path contract

BPR expects `--data_path` to end with `/` and dataset name to match its directory:

```bash
cd /workspace/dataLeakageRec/BPR
python test.py --data_path /workspace/datasets/ --data movielens --test_year 5 --num_years_added 0 --gpu -1
```

This command is a compatibility smoke test only until seed control and runtime logging are added. Do not treat its output as final reproduction.

Verified seeded smoke test on MovieLens:

```bash
python test.py --data_path /workspace/datasets/ --data movielens --test_year 5 --num_years_added 0 --gpu -1 --seed 42 --epochs 1 --max_test_users 10
```

Observed result:

```text
1 epoch: 489.40 seconds
HR@20: 0.0
NDCG@20: 0.0
```

The run completed successfully. Zero metrics are expected from this one-epoch, ten-user compatibility check and must not be compared with paper results. Full default training uses 300 epochs and all 3,171 test users; CPU runtime is therefore expected to be substantially longer.


## Next steps

Run in this order:

1. Verify imports and mounted files.
2. Run loader smoke test without TensorFlow training.
3. Run one BPR compatibility smoke test.
4. Record errors, model configuration, and runtime.
5. Add seed control and CSV logging.
6. Run three seeds for initial accuracy validation.
7. Run ten seeds only after one complete run is reproducible.
8. Compare mean, standard deviation, and runtime against the paper protocol.

Paper 01 reports HR@20 and NDCG@20. It averages three random trials for accuracy and uses seven trials for recommendation-list similarity. Exact seed values are not reported.

Use the same project seed list for every leakage condition:

```text
0, 1, 2, 3, 4, 5, 6, 7, 8, 9
```

Keep dataset, model, hyperparameters, test year, `num_years_added`, and seed list fixed when comparing conditions. Save one row per run:

```text
model,dataset,test_year,num_years_added,seed,hr20,ndcg20,train_seconds,eval_seconds,status
```

The original BPR script does not expose one common seed for Python, NumPy, and TensorFlow and uses deprecated `np.int`. Do not claim paper reproduction from a single seed or smoke test.

## Scope

- Python 3.6 / TensorFlow 1.14 base image.
- BPR and NeuMF dependencies only.
- Dataset stays host-mounted and is not copied into image.
- SASRec and LightGCN require separate dependency validation.
- Paper hardware and exact seeds are not reported; record container and host details in each run.
