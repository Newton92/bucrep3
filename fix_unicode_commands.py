# fix_all_commands.py
import os
import glob
import re

def fix_command_file(file_path):
    """Corrige un fichier de commande pour éviter les problèmes d'encodage"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modifications = []
    
    # 1. Remplacer self.style.SUCCESS et self.style.WARNING
    content = re.sub(
        r'self\.stdout\.write\(self\.style\.SUCCESS\(([^)]+)\)\)',
        r'self.stdout.write("[SUCCESS] " + \1)',
        content
    )
    
    content = re.sub(
        r'self\.stdout\.write\(self\.style\.WARNING\(([^)]+)\)\)',
        r'self.stdout.write("[WARNING] " + \1)',
        content
    )
    
    content = re.sub(
        r'self\.stdout\.write\(self\.style\.INFO\(([^)]+)\)\)',
        r'self.stdout.write("[INFO] " + \1)',
        content
    )
    
    content = re.sub(
        r'self\.stdout\.write\(self\.style\.ERROR\(([^)]+)\)\)',
        r'self.stdout.write("[ERROR] " + \1)',
        content
    )
    
    # 2. Remplacer les caractères Unicode
    unicode_replacements = {
        '✓': '[OK]',
        '↻': '[UPD]', 
        '⏭️': '[EXIST]',
        '📋': '[NEW]',
        '⚠': '[WARN]',
        '🔧': '[TOOL]',
        '📊': '[STATS]',
        '🎯': '[TARGET]',
        '🚀': '[LAUNCH]',
        '🔍': '[SEARCH]',
        '✅': '[DONE]',
        '❌': '[FAIL]',
        '•': '-',
        '═': '=',
        '─': '-',
    }
    
    for unicode_char, ascii_replacement in unicode_replacements.items():
        if unicode_char in content:
            content = content.replace(unicode_char, ascii_replacement)
            modifications.append(f"  - Remplacé '{unicode_char}' par '{ascii_replacement}'")
    
    # 3. Supprimer les appels à style() dans f-strings
    content = re.sub(
        r'f"\{self\.style\.\w+\(([^}]+)\)\}"',
        r'f"[STYLE] \1"',
        content
    )
    
    # Sauvegarder si des modifications ont été faites
    if modifications:
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {os.path.basename(file_path)}")
        for mod in modifications:
            print(f"  {mod}")
        
        # Remplacer le fichier original
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    else:
        print(f"✓ {os.path.basename(file_path)} (aucun changement nécessaire)")
        return False

def fix_all_commands():
    """Corrige tous les fichiers de commandes"""
    print("Correction des fichiers de commandes pour éviter les problèmes d'encodage...")
    print("="*70)
    
    # Trouver tous les fichiers de commandes
    command_files = glob.glob('main/management/commands/import_*.py')
    command_files += glob.glob('main/management/commands/*.py')  # Tous les fichiers
    
    fixed_count = 0
    
    for file_path in command_files:
        if fix_command_file(file_path):
            fixed_count += 1
    
    print("\n" + "="*70)
    print(f"Résumé: {fixed_count}/{len(command_files)} fichiers corrigés")
    print("\nRecommandations:")
    print("1. Pour les commandes, utilisez toujours self.stdout.write() directement")
    print("2. Évitez les caractères Unicode (✓, ⚠, etc.)")
    print("3. Utilisez des préfixes ASCII: [OK], [ERROR], [WARNING]")
    print("4. Testez via: python manage.py <command> --dry-run")

if __name__ == "__main__":
    fix_all_commands()