#!/usr/bin/env python3
"""Validate release metadata, portable skill metadata, links, and private leakage."""
from __future__ import annotations
import hashlib, json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
PRIVATE=(r"/Users/", r"/home/[^/]+/", r"\.pi-personal", r"AI_RUNTIME_PROFILE", r"DISCORD", r"HPPM", r"obsidian", r"\bvault\b", r"\balex\b", r"alex-", r"github-open-pr", r"writing-voice-check", r"commit-message", r"writing-editor", r"plugins/")
TEXT={".md", ".py", ".json", ".yml", ".yaml", ".toml", ".ini", ".sh"}
IGNORED={".git",".venv","__pycache__",".mypy_cache",".pytest_cache","site"}
def shipped():
 for p in ROOT.rglob("*"):
  if any(x in IGNORED for x in p.parts): continue
  if p.is_file() or p.is_symlink(): yield p
def covered(rel, entries):
 return any(rel==e.get("path") or rel.startswith(e.get("path_prefix", "\0")) for e in entries)
def validate_writing_policy(errors):
 roots=[ROOT/'packages/writing-check/vale',ROOT/'skills/writing/writing-check/vale']
 try: manifests=[json.loads((root/'profiles.json').read_text()) for root in roots]
 except (OSError,json.JSONDecodeError) as exc: errors.append(f'invalid Writing Check manifest: {exc}'); return
 if manifests[0] != manifests[1]: errors.append('Writing Check manifests differ between package and skill copies'); return
 rules=manifests[0].get('rules')
 if not isinstance(rules,dict) or not rules: errors.append('Writing Check manifest has no rule digests'); return
 declared=set()
 for name,metadata in rules.items():
  if not isinstance(metadata,dict) or not isinstance(metadata.get('path'),str) or not isinstance(metadata.get('sha256'),str): errors.append(f'invalid Writing Check rule metadata: {name}'); continue
  rel=metadata['path']; declared.add(rel)
  for root in roots:
   path=root/rel
   if not path.is_file(): errors.append(f'missing Writing Check rule: {path.relative_to(ROOT)}'); continue
   digest=hashlib.sha256(path.read_bytes()).hexdigest()
   if digest != metadata['sha256']: errors.append(f'Writing Check rule digest mismatch: {path.relative_to(ROOT)}')
 for root in roots:
  actual={p.relative_to(root).as_posix() for p in (root/'styles/GoogleDocs').glob('*.yml')}
  if actual != declared: errors.append(f'Writing Check rule inventory mismatch: {root.relative_to(ROOT)}')
def main():
 errors=[]
 try: inventory=json.loads((ROOT/'provenance.json').read_text())
 except (OSError,json.JSONDecodeError) as exc: print(f"invalid provenance: {exc}"); return 1
 for key in ('schema','source_revision','decision','entries','excluded'):
  if not inventory.get(key): errors.append(f'provenance missing {key}')
 entries=inventory.get('entries',[])
 for e in entries:
  if not e.get('origin') or not e.get('license'): errors.append(f"provenance entry lacks origin/license: {e}")
 for p in shipped():
  rel=p.relative_to(ROOT).as_posix()
  if not covered(rel,entries): errors.append(f'provenance missing shipped path: {rel}')
  if p.is_symlink():
   if rel != 'CLAUDE.md' or p.readlink().as_posix() != 'AGENTS.md':
    errors.append(f'unapproved symlink in public artifact: {rel}')
  elif p.suffix in TEXT:
   text=p.read_text(encoding='utf-8')
   # Validators and tests may name forbidden tokens as negative assertions.
   if rel not in {'provenance.json','scripts/validate.py'} and not rel.startswith('tests/'):
    for token in PRIVATE:
     if re.search(token,text,re.I): errors.append(f'{rel}: private token {token}')
 for p in ROOT.glob('skills/*/*/SKILL.md'):
  text=p.read_text(); m=re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: .+\n---\n',text,re.S)
  if not m or m.group(1)!=p.parent.name: errors.append(f'{p.relative_to(ROOT)}: invalid metadata')
 for p in ROOT.rglob('*.md'):
  if any(x in IGNORED for x in p.parts): continue
  for link in re.findall(r'\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)',p.read_text()):
   if '://' not in link and not (p.parent/link).exists(): errors.append(f'{p.relative_to(ROOT)}: missing {link}')
 validate_writing_policy(errors)
 if '--copied' not in sys.argv:
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'artifact'; shutil.copytree(ROOT,out,ignore=shutil.ignore_patterns('.git','__pycache__','.mypy_cache','.pytest_cache','site'))
   run=subprocess.run([sys.executable,str(out/'scripts/validate.py'),'--copied'],capture_output=True,text=True)
   if run.returncode: errors.append('copied artifact validation failed: '+run.stdout+run.stderr)
 print('\n'.join(errors) if errors else 'validation passed'); return bool(errors)
if __name__=='__main__': raise SystemExit(main())
