import json
with open('scripts/naf_extracted.json', encoding='utf-8') as f:
    data = json.load(f)
print('Sections:')
for k, v in sorted(data['sections'].items()):
    print(f'  {k}: {v}')
print(f'\nTotal codes: {len(data["codes"])}')
print('\nSample codes (first 15):')
for c in data['codes'][:15]:
    print(f'  {c}')
