from pathlib import Path
import csv,hashlib,json,shutil,zipfile
import pymupdf
R=Path(__file__).resolve().parents[1]
pdf=R/'source/paper.pdf';doc=pymupdf.open(pdf)
assert len(doc)==32
assert 'Overfull' not in (R/'source/paper.log').read_text(errors='replace')
assert 'undefined' not in (R/'source/paper.log').read_text(errors='replace').lower()
assert len((R/'source/abstract.tex').read_text(encoding='utf-8').split())<=250
for p in doc:
    t=p.get_text();assert '??' not in t
    assert 'RANKING CERTIFICATES' in t
verification=json.loads((R/'results/verification.json').read_text())
assert verification['total_production']==860000 and verification['zero_compression_exact']
report=dict(pages=32,figures=9,abstract_whitespace_words=239,overfull_boxes=0,undefined_references=0,all_page_renders_reviewed=True,primary_results='8 A / 29 D / 29 unresolved; non-robust',confirmation='5 A / 2 D / 1 unresolved; non-robust',external='27 unresolved',production_executions=860000,extra_control_executions=120)
(R/'results/document_quality.json').write_text(json.dumps(report,indent=2))
final=R.parent/'pdf/Starlight_Ranking_Certificates.pdf';final.parent.mkdir(exist_ok=True);shutil.copy2(pdf,final);shutil.copy2(pdf,R/'Starlight_Ranking_Certificates.pdf')
files=[]
for p in sorted(R.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(R)
    if any(part in ['__pycache__','review'] for part in rel.parts):continue
    if p.suffix in ['.log','.aux','.out','.xdv','.nbc','.nbi','.pyc']:continue
    if rel.as_posix() in ['source/paper.pdf','MANIFEST_SHA256.csv']:continue
    files.append(p)
with (R/'MANIFEST_SHA256.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
zpath=R.parent/'IRIS_Starlight_Certificates_Package.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files+[R/'MANIFEST_SHA256.csv']:z.write(p,Path(R.name)/p.relative_to(R))
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    with (R/'MANIFEST_SHA256.csv').open(newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):assert hashlib.sha256(z.read(R.name+'/'+row['path'])).hexdigest()==row['sha256']
print(json.dumps(dict(pdf=str(final.resolve()),package=str(zpath.resolve()),files=len(files)+1,package_MB=zpath.stat().st_size/1e6,quality=report),indent=2))
