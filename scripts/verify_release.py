#!/usr/bin/env python3
"""Check compiled release integrity and internal scope; not raw-data provenance."""
from pathlib import Path
import csv, hashlib, sys

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'REFERENCE_DATA/starlight-iris-2026'
RELEASE=ROOT/'SHA256SUMS_RELEASE.txt'

def hashfile(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def verify():
    errors=[]
    raw=DATA/'evidence/manifests/SHA256_manifest.csv'
    with raw.open(newline='',encoding='utf-8') as fh:
        source_rows=list(csv.DictReader(fh))
    for row in source_rows:
        p=(DATA/row['path']).resolve()
        if not p.is_relative_to(DATA.resolve()) or not p.is_file():
            errors.append(f'missing source file: {row["path"]}')
        elif hashfile(p)!=row['sha256'] or p.stat().st_size!=int(row['bytes']):
            errors.append(f'source digest mismatch: {row["path"]}')
    if not RELEASE.is_file():
        errors.append('missing release checksum inventory')
    else:
        listed={}
        for line in RELEASE.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            try: digest,rel=line.split('  ',1)
            except ValueError:
                errors.append('malformed checksum line');continue
            if rel in listed:errors.append('duplicate listed file '+rel)
            listed[rel]=digest
            path=(ROOT/rel).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file(): errors.append('missing release file '+rel)
            elif hashfile(path)!=digest:errors.append('release digest mismatch '+rel)
        present={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
                 if p.is_file() and not any(x in p.parts for x in
                   ['__pycache__','.pytest_cache','.git','.venv','outputs']) and
                   not p.name.endswith('.pyc') and p.name != '.coverage' and
                   p.relative_to(ROOT).as_posix()!='SHA256SUMS_RELEASE.txt' and
                   not p.relative_to(ROOT).as_posix().endswith('.egg-info/PKG-INFO')}
        # The manifest covers the shipped files; tooling may create temporary egg-info in developer environments.
        present={x for x in present if '.egg-info/' not in x}
        if set(listed)!=present:
            errors.extend('not listed: '+x for x in sorted(present-set(listed)))
            errors.extend('listed but missing from inventory scope: '+x for x in sorted(set(listed)-present))
    forbidden=[DATA/'decision_cost/caselevel.csv',DATA/'decision_cost/aggregated.csv']
    if any(p.exists() for p in forbidden): errors.append('Excluded benchmark table was re-introduced')
    if not (ROOT/'paper/Starlight_Engineering_Research_Paper.pdf').is_file(): errors.append('paper missing')
    for required in ['01_confirmed_reversal.png','02_grid_certificates.png','03_physical_heading_cohorts.png']:
        if not (ROOT/'docs/figures'/required).is_file():errors.append('missing figure '+required)
    if errors:
        print('RELEASE VERIFICATION FAILED:')
        for error in errors:print(' -',error)
        return 1
    print(f'PASS: {len(listed)} archived release files match SHA-256 checksums; {len(source_rows)} original processed-file digests match. Not an instrument/source authenticity check.')
    return 0
if __name__=='__main__':sys.exit(verify())
