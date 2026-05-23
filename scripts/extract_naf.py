"""
Extrait et analyse le contenu du document NACE_NAF ENTREPRISE FRANCAIS (1).docx
"""
import docx
import re
import json

doc = docx.Document('Documents/NACE_NAF ENTREPRISE FRANCAIS (1).docx')

# Sections NAF (lettre = catégorie principale)
SECTION_LETTERS = set('ABCDEFGHIJKLMNOPQRSTU')

# Correspondance section -> libellé catégorie
SECTION_MAP = {
    'A': 'Agriculture, chasse, sylviculture',
    'B': 'Pêche, aquaculture',
    'C': 'Industries extractives',
    'D': 'Industrie manufacturière',
    'E': 'Production et distribution d\'eau, d\'énergie',
    'F': 'Construction',
    'G': 'Commerce ; réparation automobile',
    'H': 'Hôtels et restaurants',
    'I': 'Transports et communications',
    'J': 'Activités financières',
    'K': 'Immobilier, locations, services aux entreprises',
    'L': 'Administration publique',
    'M': 'Éducation',
    'N': 'Santé et action sociale',
    'O': 'Services collectifs, sociaux et personnels',
    'P': 'Activités des ménages en tant qu\'employeurs',
    'Q': 'Activités extra-territoriales',
}

all_rows = []
for table in doc.tables:
    for row in table.rows:
        cells = [c.text for c in row.cells]
        if len(cells) < 2:
            continue
        code_raw = cells[0].strip()
        libelle_raw = cells[1].strip()

        # Handle multi-line cells
        codes = [c.strip() for c in code_raw.split('\n') if c.strip()]
        libelles = [l.strip() for l in libelle_raw.split('\n') if l.strip()]

        for i, code in enumerate(codes):
            lib = libelles[i] if i < len(libelles) else (libelles[0] if libelles else '')
            all_rows.append((code, lib))

print(f"Total rows: {len(all_rows)}")

# Identify patterns
section_re = re.compile(r'^([A-U])(\s+[A-Z]{1,2})?$')
division_re = re.compile(r'^\d{2}$')
naf_re = re.compile(r'^\d{2}[\.\d]*[A-Z]$')  # e.g. 01.1A, 21.2G

# Find all sections mentioned
sections_found = {}
for code, lib in all_rows:
    m = section_re.match(code)
    if m:
        letter = m.group(1)
        if letter not in sections_found:
            sections_found[letter] = lib[:60]

print("\nSections trouvées:")
for k, v in sorted(sections_found.items()):
    print(f"  {k}: {v}")

# Build NAF code -> section mapping
# Strategy: track current section as we scan rows
current_section = None
naf_data = []  # (section_letter, code, libelle)

for code, lib in all_rows:
    # Skip header row
    if code == 'NAF':
        continue

    # Section header: single letter (possibly followed by 2-letter abbrev)
    m = section_re.match(code)
    if m:
        letter = m.group(1)
        if letter in SECTION_LETTERS:
            current_section = letter
            continue

    # Skip rows that are 2-letter subsection codes (like 'AA', 'CA', 'CB')
    if re.match(r'^[A-Z]{2}$', code):
        continue

    # Skip empty or pure letter codes
    if not code or re.match(r'^[A-Z]+$', code):
        continue

    # This is an actual NAF code (division, group, or subclass)
    if current_section and code:
        naf_data.append((current_section, code, lib))

print(f"\nCodes NAF avec section: {len(naf_data)}")

# Show sample by section
from collections import defaultdict
by_section = defaultdict(list)
for sect, code, lib in naf_data:
    by_section[sect].append((code, lib))

for sect in sorted(by_section.keys()):
    codes = by_section[sect]
    print(f"\nSection {sect} ({len(codes)} codes):")
    for code, lib in codes[:5]:
        print(f"  {code}: {lib[:70]}")
    if len(codes) > 5:
        print(f"  ... +{len(codes)-5} autres")

# Save to JSON for use in import command
output = {'sections': {}, 'codes': []}
for sect, lib in sorted(sections_found.items()):
    output['sections'][sect] = lib
for sect, code, lib in naf_data:
    output['codes'].append({'section': sect, 'code': code, 'libelle': lib})

with open('scripts/naf_extracted.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nJSON sauvegardé: scripts/naf_extracted.json ({len(output['codes'])} codes)")
