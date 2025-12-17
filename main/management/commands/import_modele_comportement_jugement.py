# main/management/commands/import_modele_comportement_jugement.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleComportementJugement
from datetime import datetime

class Command(BaseCommand):
    help = "Importe ou met à jour les modèles de comportement de jugement"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Supprime définitivement tous les modèles existants avant l'importation"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simule l'importation sans modifier la base de données"
        )
        parser.add_argument(
            '--year',
            type=int,
            default=datetime.now().year,
            help="Année à utiliser dans les codes (défaut: année courante)"
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='MCJ',
            help="Préfixe pour les codes (défaut: MCJ pour Modèle de Comportement de Jugement)"
        )
        parser.add_argument(
            '--hard-delete',
            action='store_true',
            help="Suppression définitive (bypass safedelete) avec --clear"
        )

    def handle(self, *args, **options):
        self.stdout.write("Debut de l'importation des modeles de comportement de jugement...")
        
        # Données à importer - libellés uniques
        comportements_data = [
            "Aucune information negative n'a ete trouvee",
            "Il n'existe aucune trace d'une quelconque action de recouvrement de creances par ACREMAC a l'encontre de cette entreprise",
            "Selon nos sources, l'entreprise n'est pas en situation d'insolvabilite/procedure preliminaire/procedure de repartition des dettes",
            "Des actions en recouvrement judiciaire sont ouvertes contre l'acheteur",
            "Des actions de recouvrement a l'amiable sont ouvertes contre l'acheteur",
            "Des cas de recouvrement fermes existent chez nos sources sur l'acheteur",
            "Inconnu de nos sources",
        ]
        
        year = options['year']
        prefix = options['prefix']
        
        # Nettoyage des libellés (supprimer les doublons)
        libelles_uniques = []
        seen_libelles = set()
        
        for libelle in comportements_data:
            # Normaliser le libellé pour la comparaison
            libelle_normalise = libelle.lower().strip()
            if libelle_normalise not in seen_libelles:
                seen_libelles.add(libelle_normalise)
                libelles_uniques.append(libelle)
        
        if len(libelles_uniques) != len(comportements_data):
            duplicates = len(comportements_data) - len(libelles_uniques)
            self.stdout.write(f"[INFO] Suppression de {duplicates} doublon(s) detecte(s)")
        
        if options['clear'] and not options['dry_run']:
            self.clear_existing_data(options['hard_delete'])
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        if not options['dry_run']:
            with transaction.atomic():
                for index, libelle in enumerate(libelles_uniques, start=1):
                    # Format: MCJ-YYYY-NN (avec NN sur 2 chiffres)
                    code_complet = f"{prefix}-{year}-{index:02d}"
                    
                    # Vérifier d'abord s'il existe déjà (même en soft-deleted)
                    existing = ModeleComportementJugement.objects.all_with_deleted().filter(
                        code=code_complet
                    ).first()
                    
                    if existing:
                        if existing.deleted is not None:
                            # Restaurer l'entrée soft-deleted
                            existing.libelle = libelle
                            existing.deleted = None
                            existing.save()
                            self.stdout.write(f"[RESTORE] Restaure : {code_complet}")
                            self.stdout.write(f"         Libelle : {libelle}")
                            updated_count += 1
                        elif existing.libelle != libelle:
                            # Mettre à jour l'entrée existante
                            existing.libelle = libelle
                            existing.save()
                            self.stdout.write(f"[UPD] Mis a jour : {code_complet}")
                            self.stdout.write(f"      Libelle : {libelle}")
                            updated_count += 1
                        else:
                            # Identique, on skip
                            self.stdout.write(f"[SKIP] Deja a jour : {code_complet}")
                            skipped_count += 1
                    else:
                        # Créer nouvelle entrée
                        ModeleComportementJugement.objects.create(
                            code=code_complet,
                            libelle=libelle
                        )
                        created_count += 1
                        self.stdout.write(f"[NEW] Cree : {code_complet}")
                        self.stdout.write(f"      Libelle : {libelle}")
                        
                        # Avertir si libellé trop long
                        if len(libelle) > 250:
                            self.stdout.write(f"[WARN] Libelle long ({len(libelle)} caracteres)")
        else:
            # Mode simulation
            self.stdout.write("[INFO] Mode simulation - Aucune donnee ne sera modifiee")
            self.stdout.write("\nLibelles uniques a importer:")
            
            for index, libelle in enumerate(libelles_uniques, start=1):
                code_complet = f"{prefix}-{year}-{index:02d}"
                
                # Vérifier existence
                exists_active = ModeleComportementJugement.objects.filter(code=code_complet).exists()
                exists_deleted = ModeleComportementJugement.objects.all_with_deleted().filter(
                    code=code_complet, deleted__isnull=False
                ).exists()
                
                if exists_active:
                    status = "[EXISTE]"
                    skipped_count += 1
                elif exists_deleted:
                    status = "[SOFT-DELETED]"
                else:
                    status = "[A CREER]"
                    created_count += 1
                
                self.stdout.write(f"  {status} {code_complet}")
                self.stdout.write(f"       {libelle}")
                
                if len(libelle) > 250:
                    self.stdout.write(f"       [ATTENTION] Longueur: {len(libelle)} caracteres")
        
        # Résumé
        self.stdout.write("\n" + "="*60)
        if options['dry_run']:
            self.stdout.write("[INFO] SIMULATION - Aucune donnee modifiee")
        
        self.stdout.write("[SUCCESS] Resume de l'importation:")
        
        if options['dry_run']:
            self.stdout.write(f"\n- Libelles uniques trouves: {len(libelles_uniques)}")
            self.stdout.write(f"- Entrees a creer: {created_count}")
            self.stdout.write(f"- Entrees existantes: {skipped_count}")
        else:
            self.stdout.write(f"\n- Libelles importes: {len(libelles_uniques)}")
            self.stdout.write(f"- Entrees creees: {created_count}")
            self.stdout.write(f"- Entrees mises a jour: {updated_count}")
            self.stdout.write(f"- Entrees skip (deja a jour): {skipped_count}")
            
            total_db = ModeleComportementJugement.objects.count()
            self.stdout.write(f"- Total en base apres import: {total_db}")
        
        self.stdout.write(f"\n- Codes generes: {prefix}-{year}-01 a {prefix}-{year}-{len(libelles_uniques):02d}")
        
        # Vérification d'intégrité
        if not options['dry_run']:
            expected_total = created_count + updated_count + skipped_count
            if expected_total == len(libelles_uniques):
                self.stdout.write("\n[SUCCESS] Tous les libelles ont ete traites avec succes")
            else:
                self.stdout.write(f"\n[WARN] Mismatch: traite {expected_total} sur {len(libelles_uniques)} libelles")
    
    def clear_existing_data(self, hard_delete=False):
        """Supprime les données existantes"""
        self.stdout.write("[WARNING] Nettoyage des donnees existantes...")
        
        # Compter avant suppression
        count_active = ModeleComportementJugement.objects.count()
        count_total = ModeleComportementJugement.objects.all_with_deleted().count()
        count_deleted = count_total - count_active
        
        if hard_delete:
            # Suppression définitive
            deleted_count, _ = ModeleComportementJugement.objects.all_with_deleted().delete()
            self.stdout.write(f"[SUCCESS] Suppression definitive de {deleted_count} entrees")
            self.stdout.write(f"[INFO] Incluant {count_deleted} entrees soft-deleted")
        else:
            # Soft delete seulement
            deleted_count = ModeleComportementJugement.objects.all().delete()[0]
            self.stdout.write(f"[SUCCESS] Soft-delete de {deleted_count} entrees actives")
            self.stdout.write(f"[INFO] Total en base (avec soft-deleted): {count_total}")