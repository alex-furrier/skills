#!/usr/bin/env python3
import pathlib,re
root=pathlib.Path(__file__).resolve().parents[1]; errors=[]
for path in list((root/'docs').glob('*.md'))+[root/'README.md']:
 for link in re.findall(r'\[[^]]+\]\(([^)#]+)',path.read_text()):
  if '://' not in link and not (path.parent/link).exists(): errors.append(f'{path}: missing {link}')
print('\n'.join(errors) if errors else 'strict documentation validation passed'); raise SystemExit(bool(errors))
