"""Generate a read-only MovieLens-25M verification notebook."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "01_verify_dataset.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip("\n").splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 01 — Xác minh MovieLens-25M có sẵn

Mục tiêu: kiểm tra nguồn, license, danh sách file, checksum và cấu trúc ratings.csv. Notebook chỉ đọc; không tải, giải nén, di chuyển hoặc ghi đè dataset.

Điều kiện trước: Notebook 00 hoàn tất. Dataset dự kiến ở D:/recsys_data/raw/ml-25m/. Kết quả: manifest và checkpoint trong runs/<run_id>/."""),
    md("""## Lý thuyết — Xác minh trước khi đọc bằng Spark

- README/source xác nhận dataset và điều kiện sử dụng.
- SHA-256 nhận diện chính xác file bytes; hash tự nó không chứng minh provenance.
- Header/schema xác nhận parser đọc đúng định dạng.
- Raw GroupLens có userId,movieId,rating,timestamp; processed data Paper 01 là artifact khác, không trộn vào project dataset.
- README cấm tái phân phối. Giữ dataset ngoài Git."""),
    md("""## 1. Chọn file hiện có

Notebook mặc định không tải dữ liệu. Nếu file thiếu, cell dừng; không tự tải từ mạng."""),
    code("""from pathlib import Path
import sys

project_root = Path.cwd().resolve()
while project_root != project_root.parent and not (project_root / 'src').is_dir():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))
from src.recsys.notebook_logging import NotebookRun
from IPython import get_ipython

data_dir = Path('D:/recsys_data/raw/ml-25m')
readme_path = data_dir / 'README.txt'
ratings_path = data_dir / 'ratings.csv'
run = NotebookRun(project_root, '01_verify_dataset', metadata={'purpose': 'verify existing GroupLens data; read-only'})
run.attach_ipython(get_ipython())
print('Run ID:', run.run_id)
print('Dataset directory:', data_dir)
assert data_dir.is_dir(), f'Dataset directory missing: {data_dir}; confirm location before downloading.'
assert readme_path.is_file(), 'GroupLens README.txt missing.'
assert ratings_path.is_file()
run.log('DATA_PATHS_PRESENT', data_dir=str(data_dir), readme=str(readme_path), ratings=str(ratings_path))
run.checkpoint('data_paths', 'PASS', checks={'directory': data_dir.is_dir(), 'readme': readme_path.is_file(), 'ratings': ratings_path.is_file()})"""),
    md("""## 2. README, provenance and license

README states dataset version, expected count, usage restrictions and citation. Check claims before trusting the local folder."""),
    code("""import hashlib

readme_text = readme_path.read_text(encoding='utf-8', errors='replace')
claims = {
    'dataset_name': 'ml-25m' in readme_text,
    'expected_rating_count': '25000095 ratings' in readme_text,
    'usage_license_section': 'Usage License' in readme_text,
    'no_redistribution_clause': 'may not redistribute the data' in readme_text,
    'required_citation': '10.1145/2827872' in readme_text,
}
print('README claim checks:', claims)
assert all(claims.values()), 'README does not match expected GroupLens ml-25m record; inspect source.'
run.log('README_LICENSE_CHECK', claims=claims)
run.checkpoint('readme_license', 'PASS', checks=claims, note='Source, version, redistribution restriction and citation checked.')"""),
    md("""## 3. File inventory, SHA-256, header and row count

SHA-256 reads in blocks, not all 678 MB into RAM. CSV line count reads bytes; Notebook 02 will independently count records through Spark."""),
    code("""import csv
import hashlib
import json
import time

expected_bytes = 678260987
expected_sha256 = '9C85525758597DCA76E8D98CEBB9C13E018C2317B09A0878B6D383179526E385'
expected_rows = 25000095
size_bytes = ratings_path.stat().st_size
digest = hashlib.sha256()
line_count = 0
started = time.perf_counter()
with ratings_path.open('rb') as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
        digest.update(block)
        line_count += block.count(bytes([10]))
sha256 = digest.hexdigest()
with ratings_path.open('r', encoding='utf-8', newline='') as stream:
    header = next(csv.reader(stream))
expected_header = ['userId', 'movieId', 'rating', 'timestamp']
manifest = {
    'dataset': 'MovieLens-25M raw / ml-25m',
    'source_page': 'https://grouplens.org/datasets/movielens/25m/',
    'archive_url': 'https://files.grouplens.org/datasets/movielens/ml-25m.zip',
    'data_directory': str(data_dir),
    'ratings_file': str(ratings_path),
    'ratings_size_bytes': size_bytes,
    'ratings_sha256': sha256,
    'ratings_csv_header': header,
    'ratings_rows_by_line_count': line_count - 1,
    'readme_sha256': hashlib.sha256(readme_path.read_bytes()).hexdigest(),
    'readme_claim_checks': claims,
    'elapsed_seconds': round(time.perf_counter() - started, 2),
    'redistribution_allowed': False,
}
checks = {
    'expected_size': size_bytes == expected_bytes,
    'expected_sha256': sha256.lower() == expected_sha256.lower(),
    'expected_header': header == expected_header,
    'expected_rows': line_count - 1 == expected_rows,
}
files = {p.name: p.stat().st_size for p in sorted(data_dir.iterdir()) if p.is_file()}
print('Files:', files)
print('Ratings verification:', manifest)
print('Checks:', checks)
assert all(checks.values()), 'Dataset validation failed. Preserve files; do not auto-replace or download.'
manifest_path = run.run_dir / 'dataset_manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
run.checkpoint('dataset_verified', 'PASS', checks={**checks, 'readme_claim_checks': claims, 'manifest_path': str(manifest_path)}, note='Existing raw GroupLens dataset verified read-only; Spark row count repeats in Notebook 02.')
run.log('DATASET_VERIFIED', file_inventory=files, **manifest)
print('Manifest saved:', manifest_path)"""),
    md("""## 4. Kết luận

L1 xác nhận README/license và tính toàn vẹn file hiện có. Notebook 02 phải xác nhận schema/count bằng Spark. Dataset không được commit hoặc redistribute."""),
    code("""summary = {'dataset_verified': True, 'ratings_rows': manifest['ratings_rows_by_line_count'], 'ratings_sha256': sha256, 'manifest_path': str(manifest_path)}
run.finish('COMPLETED', summary=summary)
print('L1 PASS — README, license, size, SHA-256, CSV header and line count verified.')"""),
]

for index, cell in enumerate(cells):
    cell['id'] = f'cell-{index + 1:03d}'
    if cell['cell_type'] == 'code':
        compile(''.join(cell['source']), f'notebook-cell-{index + 1}', 'exec')
notebook = {
    'cells': cells,
    'metadata': {'kernelspec': {'display_name': 'Python 3.14 (BigData RecSys .venv)', 'language': 'python', 'name': 'recsys-project-venv'}, 'language_info': {'name': 'python'}},
    'nbformat': 4,
    'nbformat_minor': 5,
}
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Created {OUT} with {len(cells)} cells; all code cells compile')


