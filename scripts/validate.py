#!/usr/bin/env python3
"""Validate release metadata, portable skill metadata, links, and private leakage."""
from __future__ import annotations
import json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
PRIVATE=(r"/Users/", r"/home/[^/]+/", r"\.pi-personal", r"AI_RUNTIME_PROFILE", r"DISCORD", r"HPPM", r"obsidian", r"\bvault\b", r"\balex\b", r"alex-", r"github-open-pr", r"writing-voice-check", r"commit-message", r"writing-editor", r"plugins/")
TEXT={".md", ".py", ".json", ".yml", ".yaml", ".toml", ".ini", ".sh"}
IGNORED={".git","__pycache__",".pytest_cache","site"}
def shipped():
 for p in ROOT.rglob("*"):
  if any(x in IGNORED for x in p.parts): continue
  if p.is_file() or p.is_symlink(): yield p
def covered(rel, entries):
 return any(rel==e.get("path") or rel.startswith(e.get("path_prefix", "\0")) for e in entries)
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
 if '--copied' not in sys.argv:
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'artifact'; shutil.copytree(ROOT,out,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','site'))
   run=subprocess.run([sys.executable,str(out/'scripts/validate.py'),'--copied'],capture_output=True,text=True)
   if run.returncode: errors.append('copied artifact validation failed: '+run.stdout+run.stderr)
 print('\n'.join(errors) if errors else 'validation passed'); return bool(errors)
if __name__=='__main__': raise SystemExit(main())
