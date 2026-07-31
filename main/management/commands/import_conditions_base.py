# management/commands/import_conditions_base.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.translation import gettext_lazy as _
from main.models import ListeConditionAchat, ListeConditionVente


class Command(BaseCommand):
    help = 'Import des données de base pour les conditions d\'achat et vente'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['achat', 'vente', 'all'],
            default='all',
            help='Type de données à importer (achat, vente, all)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les données existantes avant import',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler sans enregistrer en base',
        )

    def handle(self, *args, **options):
        import_type = options.get('type', 'all')
        clear_data = options.get('clear', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write("="*60)
        self.stdout.write("IMPORT DES CONDITIONS D'ACHAT ET VENTE")
        self.stdout.write("="*60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE SIMULATION - Pas de sauvegarde en base"))
        
        try:
            if import_type in ['achat', 'all']:
                self.import_conditions_achat(clear_data, dry_run)
            
            if import_type in ['vente', 'all']:
                self.import_conditions_vente(clear_data, dry_run)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def import_conditions_achat(self, clear_data, dry_run):
        """Importe les conditions d'achat"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CONDITIONS D'ACHAT")
        self.stdout.write("="*50)
        
        # Données à importer : (nom_en, nom_fr)
        CONDITIONS_ACHAT = [
            ("1- Cash payment",                              "1- Paiement comptant"),
            ("2- Payment on receipt",                        "2- Paiement à réception"),
            ("3- Payment by bank transfer",                  "3- Paiement par virement bancaire"),
            ("4- Payment against documents",                 "4- Paiement contre documents"),
            ("5- Documentary credit",                        "5- Crédit documentaire"),
            ("6- Term letter of credit",                     "6- Lettre de crédit à terme"),
            ("7- Demand letter of credit",                   "7- Lettre de crédit à vue"),
            ("8- Payment term from 30 to 60 days BL date",  "8- Délai de paiement de 30 à 60 jours date BL"),
            ("9- Payment term from 60 to 90 days date LB",  "9- Délai de paiement de 60 à 90 jours date LB"),
            ("10- Payment term from 90 to 120 days date BL","10- Délai de paiement de 90 à 120 jours date BL"),
        ]

        if dry_run:
            self.stdout.write(f"\n{len(CONDITIONS_ACHAT)} conditions d'achat à importer:")
            for nom_en, nom_fr in CONDITIONS_ACHAT:
                self.stdout.write(f"  EN: {nom_en}  |  FR: {nom_fr}")
            return

        # Vérifier le modèle
        try:
            model_fields = [f.name for f in ListeConditionAchat._meta.fields]
            self.stdout.write(f"Champs du modèle: {model_fields}")
        except Exception:
            self.stdout.write(self.style.WARNING("Le modèle ListeConditionAchat n'existe pas ou a un problème"))
            return

        # Nettoyer si demandé
        if clear_data:
            self.stdout.write("Suppression des données existantes...")
            try:
                deleted = ListeConditionAchat.objects.all().delete()
                if isinstance(deleted, tuple):
                    deleted = deleted[0]
                self.stdout.write(self.style.SUCCESS(f"✓ {deleted} conditions d'achat supprimées"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Impossible de supprimer: {str(e)[:100]}"))

        # Importer les données
        created = 0
        errors = 0
        skipped = 0

        for nom_en, nom_fr in CONDITIONS_ACHAT:
            try:
                obj, is_created = ListeConditionAchat.objects.get_or_create(
                    nom_en=nom_en,
                    defaults={"nom": nom_en, "nom_fr": nom_fr, "nom_en": nom_en},
                )
                if not is_created:
                    # Mettre à jour nom_fr si manquant
                    updated = False
                    if not obj.nom_fr:
                        obj.nom_fr = nom_fr
                        updated = True
                    if not obj.nom_en:
                        obj.nom_en = nom_en
                        updated = True
                    if updated:
                        obj.save()
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"↺ {nom_en} (existe déjà)"))
                else:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {nom_en}"))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"✗ {nom_en}: {str(e)[:80]}"))
        
        # Résumé
        self.stdout.write("\n" + "-"*40)
        self.stdout.write(f"Créés: {created}")
        self.stdout.write(f"Déjà existants: {skipped}")
        self.stdout.write(f"Erreurs: {errors}")
        self.stdout.write(f"Total en base: {ListeConditionAchat.objects.count()}")
    
    def import_conditions_vente(self, clear_data, dry_run):
        """Importe les conditions de vente"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CONDITIONS DE VENTE")
        self.stdout.write("="*50)

        # Données à importer : (nom_en, nom_fr)
        # nom = nom_en (clé technique), nom_fr = label FR, nom_en = label EN
        CONDITIONS_VENTE = [
            # ── Paiement immédiat ──────────────────────────────────────────
            ("1- Cash payment",                                   "1- Paiement comptant en espèces"),
            ("2- Payment by cheque",                              "2- Paiement par chèque"),
            ("3- Payment by credit/debit card",                   "3- Paiement par carte de crédit/débit"),
            ("4- Payment by bank transfer",                       "4- Paiement par virement bancaire"),
            # ── Instruments de crédit ──────────────────────────────────────
            ("5- Bill of exchange",                               "5- Lettre de change"),
            ("6- Promissory note",                                "6- Billet à ordre"),
            ("7- Commercial paper",                               "7- Effets de commerce"),
            # ── Délais de paiement ─────────────────────────────────────────
            ("8- Payment term 15 to 30 days from invoice date",   "8- Délai de paiement de 15 à 30 jours date facture"),
            ("9- Payment term 30 to 60 days from invoice date",   "9- Délai de paiement de 30 à 60 jours date facture"),
            ("10- Payment term 60 to 90 days from invoice date",  "10- Délai de paiement de 60 à 90 jours date facture"),
            ("11- Payment term over 90 days from invoice date",   "11- Délai de paiement supérieur à 90 jours date facture"),
        ]

        if dry_run:
            self.stdout.write(f"\n{len(CONDITIONS_VENTE)} conditions de vente à importer:")
            for nom_en, nom_fr in CONDITIONS_VENTE:
                self.stdout.write(f"  EN: {nom_en}  |  FR: {nom_fr}")
            return

        # Vérifier le modèle
        try:
            model_fields = [f.name for f in ListeConditionVente._meta.fields]
            self.stdout.write(f"Champs du modèle: {model_fields}")
        except Exception:
            self.stdout.write(self.style.WARNING("Le modèle ListeConditionVente n'existe pas ou a un problème"))
            return

        # Nettoyer si demandé
        if clear_data:
            self.stdout.write("Suppression des données existantes...")
            try:
                deleted = ListeConditionVente.objects.all().delete()
                if isinstance(deleted, tuple):
                    deleted = deleted[0]
                self.stdout.write(self.style.SUCCESS(f"✓ {deleted} conditions de vente supprimées"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Impossible de supprimer: {str(e)[:100]}"))

        # Importer les données
        created = 0
        errors = 0
        skipped = 0

        for nom_en, nom_fr in CONDITIONS_VENTE:
            try:
                obj, is_created = ListeConditionVente.objects.get_or_create(
                    nom_en=nom_en,
                    defaults={"nom": nom_en, "nom_fr": nom_fr, "nom_en": nom_en},
                )
                if not is_created:
                    updated = False
                    if not obj.nom_fr:
                        obj.nom_fr = nom_fr
                        updated = True
                    if not obj.nom_en:
                        obj.nom_en = nom_en
                        updated = True
                    if updated:
                        obj.save()
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"↺ {nom_en} (existe déjà)"))
                else:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {nom_en}"))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"✗ {nom_en}: {str(e)[:80]}"))
        
        # Résumé
        self.stdout.write("\n" + "-"*40)
        self.stdout.write(f"Créés: {created}")
        self.stdout.write(f"Déjà existants: {skipped}")
        self.stdout.write(f"Erreurs: {errors}")
        self.stdout.write(f"Total en base: {ListeConditionVente.objects.count()}")


# Version simplifiée avec SQL brut
class CommandSQL(BaseCommand):
    """Version utilisant SQL brut pour contourner les problèmes"""
    help = 'Import SQL des conditions d\'achat et vente'
    
    def handle(self, *args, **options):
        self.stdout.write("Import via SQL brut...")
        
        CONDITIONS_ACHAT_SQL = [
            ("1",  "1- Cash payment"),
            ("2",  "2- Payment on receipt"),
            ("3",  "3- Payment by bank transfer"),
            ("4",  "4- Payment against documents"),
            ("5",  "5- Documentary credit"),
            ("6",  "6- Term letter of credit"),
            ("7",  "7- Demand letter of credit"),
            ("8",  "8- Payment term from 30 to 60 days BL date"),
            ("9",  "9- Payment term from 60 to 90 days date LB"),
            ("10", "10- Payment term from 90 to 120 days date BL"),
        ]
        
        CONDITIONS_VENTE_SQL = [
            ("1", "Espèces"),
            ("2", "Chèque"),
            ("3", "Virement bancaire"),
            ("4", "Effets de commerce papier"),
            ("5", "Lettre de Change"),
            ("6", "Billet à ordre"),
            ("7", "Carte de credit/debit"),
            ("8", "Délais de paiement de 15 à 30 jours avec pénalités de retard"),
            ("9", "Délais de paiement de 30 à 60 jours avec pénalités de retard"),
            ("10", "Délais de paiement de 60 à 90 jours avec pénalités de retard"),
        ]
        
        with connection.cursor() as cursor:
            # 1. Conditions d'achat
            self.stdout.write("\nImport conditions d'achat...")
            for code, nom in CONDITIONS_ACHAT_SQL:
                try:
                    cursor.execute("""
                        INSERT INTO main_listeconditionachat (code, nom)
                        VALUES (%s, %s)
                        ON CONFLICT (code) DO NOTHING;
                    """, [code, nom])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}"))
                except Exception as e:
                    # Si la table n'a pas de code, essayer sans
                    try:
                        cursor.execute("""
                            INSERT INTO main_listeconditionachat (nom)
                            VALUES (%s);
                        """, [nom])
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}"))
                    except:
                        self.stdout.write(self.style.ERROR(f"  ✗ {nom}"))
            
            # 2. Conditions de vente
            self.stdout.write("\nImport conditions de vente...")
            for code, nom in CONDITIONS_VENTE_SQL:
                try:
                    cursor.execute("""
                        INSERT INTO main_listeconditionvente (code, nom)
                        VALUES (%s, %s)
                        ON CONFLICT (code) DO NOTHING;
                    """, [code, nom])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}"))
                except Exception as e:
                    # Si la table n'a pas de code, essayer sans
                    try:
                        cursor.execute("""
                            INSERT INTO main_listeconditionvente (nom)
                            VALUES (%s);
                        """, [nom])
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}"))
                    except:
                        self.stdout.write(self.style.ERROR(f"  ✗ {nom}"))
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT TERMINÉ")
        self.stdout.write("="*50)