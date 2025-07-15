import re

settings_path = "settings.py"
output_path = ".env.example"

# Regex pour capter les appels à env()
env_pattern = re.compile(r"env(?:\.bool|\.list)?\(\s*[\"']([\w_]+)[\"']")

# Dictionnaire pour stocker les variables trouvées
env_vars = set()

with open(settings_path, encoding="utf-8") as file:
    content = file.read()
    matches = env_pattern.findall(content)
    env_vars.update(matches)

# Créer le .env.example avec des valeurs fictives
with open(output_path, "w", encoding="utf-8") as f:
    for var in sorted(env_vars):
        f.write(f"{var}=your_value_here\n")

print(f".env.example généré avec {len(env_vars)} variables.")
