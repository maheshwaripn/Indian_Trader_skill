"""Check relative Markdown links and portable skill headers without network."""
import re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
errors=[]
for p in root.rglob('*.md'):
    if any(x in p.parts for x in ('.git','.venv','workspace')):
        continue
    text=p.read_text()
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if '://' in link or link.startswith('#'):
            continue
        target=(p.parent/link.split('#')[0]).resolve()
        if not target.exists():errors.append(f'{p.relative_to(root)}: missing {link}')
for p in (root/'skills').glob('*/SKILL.md'):
    text=p.read_text()
    if not re.match(r'^---\nname: [a-z0-9-]+\ndescription: .+\n---\n',text):
        errors.append(f'invalid skill header {p}')
if errors:
    raise SystemExit('\n'.join(errors))
print('Relative documentation links and skill headers pass.')
