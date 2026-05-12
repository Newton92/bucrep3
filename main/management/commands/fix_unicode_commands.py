# fix_unicode_commands.py
import os
import glob

def fix_unicode_in_commands():
    """Remplace les caractères Unicode problématiques dans toutes les commandes"""
    
    # Caractères à remplacer
    unicode_replacements = {
        '[OK]': '[OK]',
        '[UPD]': '[UPD]',
        '[EXIST]': '[EXIST]',
        '[NEW]': '[NEW]',
        '[WARN]': '[WARN]',
        '[TOOL]': '[TOOL]',
        '[STATS]': '[STATS]',
        '[TARGET]': '[TARGET]',
        '[LAUNCH]': '[LAUNCH]',
        '[SEARCH]': '[SEARCH]',
        '[DONE]': '[DONE]',
        '[FAIL]': '[FAIL]',
        '-': '-',
        '=': '=',
        '-': '-',
        '└': '|--',
        '├': '|--',
        '│': '|',
        '┌': '+-',
        '┐': '-+',
        '┘': '-+',
        '┴': '-+-',
        '┬': '-+-',
        '┤': '-|',
        '├': '|-',
    }
    
    # Trouver tous les fichiers de commandes
    command_files = glob.glob('main/management/commands/import_*.py')
    
    for file_path in command_files:
        print(f"Traitement de: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les caractères Unicode
        modified = False
        for unicode_char, ascii_replacement in unicode_replacements.items():
            if unicode_char in content:
                content = content.replace(unicode_char, ascii_replacement)
                modified = True
        
        if modified:
            # Sauvegarder l'original
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  [OK] Fichier modifié, backup: {backup_path}")
        else:
            print(f"  [OK] Aucun changement nécessaire")
    
    print(f"\n[DONE] {len(command_files)} fichiers traités")

if __name__ == "__main__":
    fix_unicode_in_commands()