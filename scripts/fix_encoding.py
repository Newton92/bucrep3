"""
Vérifie les vrais codepoints Unicode dans le JSON et le corrige si nécessaire.
"""
import json, sys

with open('scripts/naf_extracted.json', encoding='utf-8') as f:
    data = json.load(f)

# Check first section libelle for replacement chars
sample = data['sections']['B']
print(f"Section B raw: {repr(sample)}")
print(f"Has replacement char (U+FFFD): {chr(0xFFFD) in sample}")

# Check first code libelle
sample2 = data['codes'][2]['libelle']
print(f"\nCode 01.1A libelle raw: {repr(sample2)}")
print(f"Has replacement char: {chr(0xFFFD) in sample2}")

# The Word doc seems to use correct French. The terminal shows ? but the data may be fine.
# Let's check a known French word: céréales should appear in code 01.1A
# c=0x63, é=0xe9, r=0x72, é=0xe9, a=0x61, l=0x6c, e=0x65, s=0x73
expected = "céréales"
actual_codes = [ord(c) for c in sample2]
print(f"\nCodepoints in 01.1A libelle: {[hex(c) for c in actual_codes]}")

# The fix: use cp1252 decoding from the raw XML in docx
import docx
doc = docx.Document('Documents/NACE_NAF ENTREPRISE FRANCAIS (1).docx')
# Get first table first real data
for table in doc.tables:
    for row in table.rows:
        cells = [c.text for c in row.cells]
        if len(cells) >= 2 and cells[0].strip() == '01.1A':
            print(f"\n01.1A raw from docx: {repr(cells[1])}")
            print(f"Codepoints: {[hex(ord(c)) for c in cells[1][:20]]}")
            break
