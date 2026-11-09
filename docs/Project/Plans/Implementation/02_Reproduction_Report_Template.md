# Reproduction Report Template

Copy file này thành `01_repository_reproduction.md`, `02_repository_reproduction.md` hoặc tên tương ứng. Mỗi kết luận phải có bằng chứng command/output/file.

## Paper and artifact

- Paper:
- Official repository/artifact URL:
- Accessed date:
- Commit/tag/hash:
- License:

## Environment

- OS:
- Python:
- Java:
- Framework/library versions:
- CPU/GPU/RAM:
- Dataset path and checksum:
- Environment file or install command:

## Protocol extracted from paper

- Dataset and filters:
- Train/validation/test split:
- Model and parameters:
- Metric and cutoff:
- Seed:
- Hardware/runtime:
- Items not reported:

## Commands

```text
# clone/pin command
# install command
# smoke-test command
# full command, only after smoke test
```

## Results

- Smoke test status: `pass` / `fail` / `blocked`
- Full run status:
- Output files:
- Runtime:
- Error log:
- Result matches paper: `yes` / `partial` / `no` / `not_assessed`

## Difference ledger

| Dimension | Paper | Local run | Consequence |
|---|---|---|---|
| Dataset | | | |
| Preprocessing | | | |
| Split | | | |
| Model | | | |
| Metric | | | |
| Seed | | | |
| Hardware | | | |

## Classification

Use exactly one:

- `faithful_reproduction`
- `partial_reproduction`
- `method_informed_implementation`
- `blocked`

Reason:

## Evidence links

- Repository files:
- Local logs:
- Paper pages/sections:
