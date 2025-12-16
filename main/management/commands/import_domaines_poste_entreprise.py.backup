# management/commands/import_domaines_poste_entreprise.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import DomaineEntreprise, PosteEntreprise


class Command(BaseCommand):
    help = 'Import Domaines et Postes d\'entreprise depuis POST_TOTAL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database',
        )
        parser.add_argument(
            '--skip-postes',
            action='store_true',
            help='Import only domaines, skip postes',
        )
        parser.add_argument(
            '--skip-domaines',
            action='store_true',
            help='Import only postes, skip domaines',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        skip_postes = options.get('skip_postes', False)
        skip_domaines = options.get('skip_domaines', False)
        
        # Structure POST_TOTAL (exemple complet avec quelques catégories)
        post_total_data = [
            # Format: (libelle_domaine, [(code_poste, libelle_poste), ...])
            (
                "01.1.0   MEMBRES DE L'EXECUTIF ET DU CORPS LEGISLATIF", 
                [
                    ("01.1.0.01", "Président de la république"),
                    ("01.1.0.02", "Chef du gouvernement"),
                    ("01.1.0.03", "Ministre, Secrétaire d'Etat et assimilés"),
                    ("01.1.0.04", "Gouverneur, Haut commissaire"),
                    ("01.1.0.05", "Député, Sénateur"),
                    ("01.1.0.06", "Maire"),
                    ("01.1.0.07", "Conseiller municipal"),
                    ("01.1.0.08", "Membre de l'exécutif et du corps législatif non classé ailleurs"),
                ]
            ),
            (
                "01.2.1   Cadres supérieurs de l'administration publique", 
                [
                    ("01.2.1.01", "Secrétaire général (ministère)"),
                    ("01.2.1.02", "Directeur de cabinet (ministre)"),
                    ("01.2.1.03", "Administrateur"),
                    ("01.2.1.04", "Inspecteur d'Etat"),
                    ("01.2.1.05", "Directeur général (Directeur national)"),
                    ("01.2.1.06", "Directeur (chef de division)"),
                    ("01.2.1.07", "Ambassadeur"),
                    ("01.2.1.08", "Chargé d'affaires"),
                    ("01.2.1.09", "Consul général"),
                    ("01.2.1.10", "Secrétaire d'ambassade"),
                    ("01.2.1.11", "Préfet"),
                    ("01.2.1.12", "Préfet de police"),
                    ("01.2.1.13", "Trésorier payeur général"),
                    ("01.2.1.14", "Cadres supérieurs de l'administration publique non classés ailleurs"),
                ]
            ),
            (
                "01.2.2   Chef traditionnel et chef de village", 
                [
                    ("01.2.2.01", "Chef coutumier"),
                    ("01.2.2.02", "Chef de village"),
                    ("01.2.2.03", "Chef de quartier"),
                ]
            ),
            (
                "01.2.3   Dirigeants et cadres supérieurs d'organismes spécialisés", 
                [
                    ("01.2.3.01", "Dirigeant de parti politique"),
                    ("01.2.3.02", "Cadre supérieur de partie politique"),
                    ("01.2.3.03", "Dirigeant syndical"),
                    ("01.2.3.04", "Cadre supérieur de syndicat"),
                    ("01.2.3.05", "Dirigeant d'organisation d'employeurs"),
                    ("01.2.3.06", "Cadre supérieur d'organisation d'employeurs"),
                    ("01.2.3.07", "Dirigeant d'organisation humanitaire, d'ONGs et d'associations"),
                    ("01.2.3.08", "Cadre supérieur d'organisation humanitaire, ONG, associations"),
                    ("01.2.3.09", "Dirigeants et cadres supérieurs d'organismes spécialisés non classés ailleurs"),
                ]
            ),
            (
                "01.3.1   Directeurs cadre de société", 
                [
                    ("01.3.1.01", "Chef d'entreprise"),
                    ("01.3.1.02", "Administrateur, gérant d'entreprise"),
                    ("01.3.1.03", "Directeur d'entreprise"),
                    ("01.3.1.04", "Directeur général d'entreprise"),
                    ("01.3.1.05", "Président directeur général"),
                    ("01.3.1.06", "Industriel"),
                    ("01.3.1.07", "Directeur, lycée et collège"),
                    ("01.3.1.08", "Recteur, université"),
                    ("01.3.1.09", "Cadre de direction"),
                    ("01.3.1.10", "Directeurs cadre de société non classés ailleurs"),
                ]
            ),
            # ... Ajoutez TOUTES les autres catégories ici de la même manière
            (
                "02.1.1   Physiciens, chimistes et assimilés",
                [
                    ("02.1.1.01", "Physicien"),
                    ("02.1.1.02", "Climatologiste, climatologue"),
                    ("02.1.1.03", "Ingénieurs météorologiste"),
                    ("02.1.1.04", "Météorologue"),
                    ("02.1.1.05", "Chimiste"),
                    ("02.1.1.06", "Géologue"),
                    ("02.1.1.07", "Ingénieur géologue"),
                    ("02.1.1.08", "Hydrologiste"),
                    ("02.1.1.09", "Physiciens, chimistes et assimilés non classés ailleurs"),
                ]
            ),
            (
                "02.1.2   Mathématiciens, statisticiens et assimilés",
                [
                    ("02.1.2.01", "Mathématicien"),
                    ("02.1.2.02", "Actuaire"),
                    ("02.1.2.03", "Statisticien"),
                    ("02.1.2.04", "Démographe"),
                    ("02.1.2.05", "Mathématiciens, statisticiens et assimilés non classés ailleurs"),
                ]
            ),
            (
                "02.1.3   Spécialistes de l'informatique",
                [
                    ("02.1.3.01", "Informaticien"),
                    ("02.1.3.02", "Programmeur"),
                    ("02.1.3.03", "Spécialistes de l'informatique non classés ailleurs"),
                ]
            ),
            (
                "02.1.4   Architectes, ingénieurs et assimilés",
                [
                    ("02.1.4.01", "Architecte"),
                    ("02.1.4.02", "Urbaniste"),
                    ("02.1.4.03", "Ingénieur, génie civil"),
                    ("02.1.4.04", "Ingénieur, génie rural"),
                    ("02.1.4.05", "Ingénieurs, ponts et chaussées"),
                    ("02.1.4.06", "Technicien supérieur, génie civil"),
                    ("02.1.4.07", "Technicien supérieur, génie rural"),
                    ("02.1.4.08", "Ingénieur électricien"),
                    ("02.1.4.09", "Ingénieur électronicien"),
                    ("02.1.4.10", "Ingénieur des télécommunications"),
                    ("02.1.4.11", "Technicien supérieur / électricien"),
                    ("02.1.4.12", "Technicien supérieur / télécommunication"),
                    ("02.1.4.13", "Ingénieur frigoriste"),
                    ("02.1.4.14", "Ingénieur mécanicien"),
                    ("02.1.4.15", "Ingénieur naval"),
                    ("02.1.4.16", "Ingénieur chimiste"),
                    ("02.1.4.17", "Technicien supérieur, chimie"),
                    ("02.1.4.18", "Ingénieur des mines"),
                    ("02.1.4.19", "Ingénieur métallurgiste"),
                    ("02.1.4.20", "Ingénieur sidérurgiste"),
                    ("02.1.4.21", "Technicien supérieur, métallurgiste"),
                    ("02.1.4.22", "Cartographe"),
                    ("02.1.4.23", "Géomètre"),
                    ("02.1.4.24", "Architectes, ingénieurs et assimilés non classés ailleurs"),
                ]
            ),
            (
                "02.2.1   Spécialistes des sciences de la vie",
                [
                    ("02.2.1.01", "Bactériologiste"),
                    ("02.2.1.02", "Biologiste"),
                    ("02.2.1.03", "Botaniste"),
                    ("02.2.1.04", "Biochimiste"),
                    ("02.2.1.05", "Ecologiste"),
                    ("02.2.1.06", "Zoologiste"),
                    ("02.2.1.07", "Anatomiste"),
                    ("02.2.1.08", "Biophysicien"),
                    ("02.2.1.09", "Pathologiste"),
                    ("02.2.1.10", "Pharmacologue"),
                    ("02.2.1.11", "Physiologiste"),
                    ("02.2.1.12", "Toxicologue"),
                    ("02.2.1.13", "Agronome"),
                    ("02.2.1.14", "Ingénieur agronome, agricole"),
                    ("02.2.1.15", "Ingénieur forestier"),
                    ("02.2.1.16", "Pédologue"),
                    ("02.2.1.17", "Spécialistes des sciences de la vie non classés ailleurs"),
                ]
            ),
            (
                "02.2.2   Médecins et assimilés",
                [
                    ("02.2.2.01", "Médecin généraliste"),
                    ("02.2.2.02", "Médecin spécialiste (chirurgie, gynécologie, pédiatre, ophtalmologue, orthopédiste, etc.)"),
                    ("02.2.2.03", "Dentiste"),
                    ("02.2.2.04", "Vétérinaire"),
                    ("02.2.2.05", "Pharmacien"),
                ]
            ),
            (
                "02.2.3   Cadres infirmiers",
                [
                    ("02.2.3.01", "Infirmier diplômé"),
                    ("02.2.3.02", "Sage-femme diplômé"),
                    ("02.2.3.03", "Cadres infirmiers non classés ailleurs"),
                ]
            ),
            (
                "02.3.1   Professeurs d'université et d'établissement d'enseignement supérieur",
                [
                    ("02.3.1.01", "Chargé de cours, université"),
                    ("02.3.1.02", "Professeur d'université (assistant, maître assistant, maître de conférence)"),
                    ("02.3.1.03", "Chercheur (attaché de recherches, chargé de recherches,"),
                    ("02.3.1.04", "Directeur de recherches, maître de recherches"),
                ]
            ),
            (
                "02.3.2   Professeur de l'enseignement secondaire",
                [
                    ("02.3.2.01", "Professeur d'enseignement secondaire"),
                ]
            ),
            (
                "02.3.3   Instituteur de l'enseignement primaire et enseignement spécialisé",
                [
                    ("02.3.3.01", "Enseignant, éducation spéciale (sourds, aveugle, handicapé, etc.)"),
                ]
            ),
            (
                "02.3.4   Autres spécialistes de l'enseignement",
                [
                    ("02.3.4.01", "Inspecteur d'enseignement (primaire ou secondaire)"),
                    ("02.3.4.02", "Conseiller pédagogique"),
                    ("02.3.4.03", "Autre spécialiste de l'enseignement NCA"),
                ]
            ),
            (
                "02.4.1   Cadres comptables",
                [
                    ("02.4.1.01", "Cadre comptable"),
                    ("02.4.1.02", "Chef comptable"),
                    ("02.4.1.03", "Expert-comptable"),
                    ("02.4.1.04", "Vérificateur de compte"),
                    ("02.4.1.05", "Cadres comptables non classés ailleurs"),
                ]
            ),
            (
                "02.4.2   Spécialistes des problèmes de personnel et de développement des carrières",
                [
                    ("02.4.2.01", "Spécialistes, gestion des ressources humaines"),
                ]
            ),
            (
                "02.4.3   Spécialistes des fonctions administratives et commerciales des entreprises non classés ailleurs",
                [
                    ("02.4.3.01", "Spécialistes des fonctions administratives et commerciales des entreprises non classés ailleurs"),
                ]
            ),
            (
                "02.4.4   Juristes",
                [
                    ("02.4.4.01", "Avocat"),
                    ("02.4.4.02", "Juge"),
                    ("02.4.4.03", "Magistrat"),
                    ("02.4.4.04", "Greffier"),
                    ("02.4.4.05", "Huissier"),
                    ("02.4.4.06", "Notaire"),
                    ("02.4.4.07", "Juriste non classé ailleurs"),
                ]
            ),
            (
                "02.4.5   Archivistes, bibliothécaires, documentalistes et assimilés",
                [
                    ("02.4.5.01", "Archivistes"),
                    ("02.4.5.02", "Conservateur"),
                    ("02.4.5.03", "Bibliothécaire"),
                    ("02.4.5.04", "Documentaliste"),
                    ("02.4.5.05", "Archivistes, bibliothécaires, documentalistes et assimilés non classés ailleurs"),
                ]
            ),
            (
                "02.5.1   Economiste",
                [
                    ("02.5.1.01", "Economiste"),
                ]
            ),
            (
                "02.5.2   Sociologues, anthropologues et assimilés",
                [
                    ("02.5.2.01", "Anthropologue"),
                    ("02.5.2.02", "Archéologue"),
                    ("02.5.2.03", "Ethnologue"),
                    ("02.5.2.04", "Criminologue"),
                    ("02.5.2.05", "Géographe"),
                    ("02.5.2.06", "Sociologue"),
                ]
            ),
            (
                "02.5.3   Philosophes, historiens et spécialistes des sciences politiques",
                [
                    ("02.5.3.01", "Historien"),
                    ("02.5.3.02", "Philosophe"),
                    ("02.5.3.03", "Politologue, spécialiste des sciences politiques"),
                ]
            ),
            (
                "02.5.4   Linguistes, traducteurs et interprètes",
                [
                    ("02.5.4.01", "Interprète"),
                    ("02.5.4.02", "Linguiste"),
                    ("02.5.4.03", "Traducteur"),
                ]
            ),
            (
                "02.5.5   Psychologue",
                [
                    ("02.5.5.01", "Psychologue"),
                ]
            ),
            (
                "02.5.6   Spécialistes du travail social",
                [
                    ("02.5.6.01", "Animateur, centre communautaire"),
                    ("02.5.6.02", "Assistant médico-social"),
                    ("02.5.6.03", "Assistant social"),
                    ("02.5.6.04", "Spécialistes du travail social non classés ailleurs"),
                ]
            ),
            (
                "02.5.7   Spécialistes des sciences sociales et humaines Non classés ailleurs",
                [
                    ("02.5.7.01", "Spécialistes des sciences sociales et humaines Non classés ailleurs"),
                ]
            ),
            (
                "02.6.1   Auteurs, journalistes et autres écrivains",
                [
                    ("02.6.1.01", "Auteurs"),
                    ("02.6.1.02", "Biographe"),
                    ("02.6.1.03", "Chroniqueur"),
                    ("02.6.1.04", "Commentateur (radio, télé, sport, etc.)"),
                    ("02.6.1.05", "Correspondant (presse, journaux, etc.)"),
                    ("02.6.1.06", "Critique"),
                    ("02.6.1.07", "Journaliste"),
                    ("02.6.1.08", "Poète"),
                    ("02.6.1.09", "Romancier"),
                    ("02.6.1.10", "scénariste"),
                    ("02.6.1.11", "Auteurs, journalistes et autres écrivains non classés ailleurs"),
                ]
            ),
            (
                "02.6.2   Sculpteurs, peintres et assimilés",
                [
                    ("02.6.2.01", "Artiste peintre"),
                    ("02.6.2.02", "Dessinateur (publicité, bandes dessinées, etc.)"),
                    ("02.6.2.03", "Sculpteur"),
                ]
            ),
            (
                "02.6.3   Compositeurs, musiciens et chanteurs",
                [
                    ("02.6.3.01", "Musicien (guitariste, pianiste, saxophoniste)"),
                    ("02.6.3.02", "Chanteur, cantatrice"),
                    ("02.6.3.03", "Compositeur"),
                ]
            ),
            (
                "02.6.4   Chorégraphes et danseurs",
                [
                    ("02.6.4.01", "Chorégraphe"),
                    ("02.6.4.02", "Danseur"),
                ]
            ),
            (
                "02.6.5   Acteurs et metteurs en scènes de cinéma, de théâtres et d'autres spectacles",
                [
                    ("02.6.5.01", "Acteur, comédien"),
                    ("02.6.4.02", "Danseur"),
                    ("02.6.5.02", "Metteur en scène (théâtre, cinéma, télévision)"),
                    ("02.6.5.03", "Réalisateur (cinéma, télévision, radio)"),
                    ("02.6.5.04", "Acteurs et metteurs en scènes de cinéma, de théâtres et d'autres spectacles non classés ailleurs"),
                ]
            ),
            (
                "02.7.0   Membres du clergé",
                [
                    ("02.7.0.01", "Personnel du culte chrétien"),
                    ("02.7.0.02", "Personnel du culte musulman (marabout, imam, maître coranique)"),
                ]
            ),
            (
                "03.1.1   Cadres de l'administration territoriale, du travail et de la sécurité Sociale",
                [
                    ("03.1.1.01", "Administrateur civil"),
                    ("03.1.1.02", "Attaché administratif"),
                    ("03.1.1.03", "Cadre supérieur de police (Commissaire, inspecteur de police)"),
                    ("03.1.1.04", "Inspecteur des affaires administratives"),
                    ("03.1.1.05", "Inspecteur du travail et des lois sociales"),
                    ("03.1.1.06", "Cadre supérieur de la sécurité sociale"),
                ]
            ),
            (
                "03.1.2   Cadres de l'Enseignement et de la recherche, de la santé et des affaires sociales",
                [
                    ("03.1.2.01", "Attaché d'intendance universitaire"),
                    ("03.1.2.02", "proviseur"),
                    ("03.1.2.03", "censeur"),
                    ("03.1.2.04", "Administrateur et attachés des hôpitaux"),
                    ("03.1.2.05", "ingénieur sanitaire"),
                    ("03.1.2.06", "Autre cadres supérieurs des affaires sociales"),
                    ("03.1.2.07", "nutritionniste"),
                    ("03.1.2.08", "Diététicien"),
                    ("03.1.2.09", "Assistant de santé, attaché de santé"),
                    ("03.1.2.10", "Assistant médical"),
                    ("03.1.2.11", "Assistant dentiste"),
                    ("03.1.2.12", "Assistant pharmacien"),
                    ("03.1.2.13", "Préparateur en pharmacie"),
                    ("03.1.2.14", "Kinésithérapeute"),
                    ("03.1.2.15", "Masseur"),
                    ("03.1.2.16", "Opticien"),
                    ("03.1.2.17", "Technicien de radiologie médicale"),
                    ("03.1.2.18", "Praticien de médecine traditionnelle et guérisseurs"),
                ]
            ),
            (
                "03.1.3   Cadres supérieurs du secteur des télécommunications, Transports, Equipement et Bâtiment",
                [
                    ("03.1.3.01", "cadre sup. des P et T (Ingénieur des P et T, Administrateur des P et T)"),
                    ("03.1.3.02", "Inspecteur mécanicien, marine marchande"),
                    ("03.1.3.03", "Officier mécanicien, navire"),
                    ("03.1.3.04", "Officier de navigation"),
                    ("03.1.3.05", "Pilote de navire"),
                    ("03.1.3.06", "Mécanicien navigant, avion"),
                    ("03.1.3.07", "Pilote d'avion"),
                    ("03.1.3.08", "Contrôleur de la circulation aérienne"),
                    ("03.1.3.09", "Technicien, sécurité aérienne"),
                    ("03.1.3.10", "Instructeur, navigation"),
                    ("03.1.3.11", "Moniteur, auto-école"),
                    ("03.1.3.12", "Courtier maritime"),
                    ("03.1.3.13", "Agent maritime"),
                    ("03.1.3.14", "Agent, dédouanement"),
                    ("03.1.3.15", "Déclarant en douane"),
                    ("03.1.3.16", "Transitaire"),
                    ("03.1.3.17", "inspecteur des T.P."),
                    ("03.1.3.18", "Ingénieur de l'équipement rural et de l'hydraulique"),
                    ("03.1.3.19", "cadre sup. et technicien de l'équipement rural"),
                ]
            ),
            (
                "03.1.4   Cadres Supérieurs des Ressources Financière, Budget, Planification, Commerce, Banque et Assurances",
                [
                    ("03.1.4.01", "Cadre supérieur des affaires économiques"),
                    ("03.1.4.02", "Inspecteur des douanes"),
                    ("03.1.4.03", "Inspecteurs des impôts"),
                    ("03.1.4.04", "Inspecteurs du trésor"),
                    ("03.1.4.05", "Autres cadre sup. des ressources financières (trésor, impôts, douanes, domaine, enregistrement)"),
                    ("03.1.4.06", "Administrateur des services fiscaux et des services financiers"),
                    ("03.1.4.07", "Planificateur"),
                    ("03.1.4.08", "Autres cadres supérieurs statisticiens et démographes"),
                    ("03.1.4.09", "Contrôleur des prix"),
                    ("03.1.4.10", "Contrôleur de qualité"),
                    ("03.1.4.11", "Cadre supérieur de banque"),
                    ("03.1.4.12", "Cadre supérieur des assurances"),
                ]
            ),
            (
                "03.1.5   Cadres Supérieurs de l'Agriculture, Elevage, Forêt, Energie, Géologie, Mines",
                [
                    ("03.1.5.01", "Conseiller agricole"),
                    ("03.1.5.02", "Conseiller forestier"),
                    ("03.1.5.03", "Vulgarisateur agricole"),
                    ("03.1.5.04", "Ingénieur et conseiller FJA (Formateur de Jeunes Agriculteurs)"),
                    ("03.1.5.05", "Autres cadres sup. de l'agriculture"),
                    ("03.1.5.06", "Autres cadres sup. des Eaux et Forêts et de pêche"),
                    ("03.1.5.07", "Autres cadres sup. de l'élevage"),
                    ("03.1.5.08", "Autres techniciens des sciences biologiques et agronomiques"),
                    ("03.1.5.09", "Autres cadres supérieurs de la géologie et des mines non classés ailleurs"),
                ]
            ),
            (
                "03.1.6   Cadres Supérieurs de la Justice, de l'Information et des Relations Extérieures",
                [
                    ("03.1.6.01", "Président de la cour d'appel"),
                    ("03.1.6.02", "Cadre sup. des affaires étrangères"),
                ]
            ),
            (
                "03.1.7   Cadres Supérieurs de l'Information, écrivains, artistes créateurs et exécutants, sports et autres cadres supérieurs non classés ailleurs",
                [
                    ("03.1.7.01", "Cadre sup. de la presse et de la communication"),
                    ("03.1.7.02", "Décorateur, dessinateur de modèle"),
                    ("03.1.7.03", "Caméraman (cinéma, télévision)"),
                    ("03.1.7.04", "Photographe (commercial, industriel, presse, publicitaire, etc.)"),
                    ("03.1.7.05", "Manageur sportif"),
                    ("03.1.7.06", "Professeur d'éducation permanente et physique"),
                    ("03.1.7.07", "Inspecteur de la jeunesse et des sports"),
                    ("03.1.7.08", "Conseiller de la jeunesse et d'animation"),
                    ("03.1.7.09", "Administrateur des affaires culturelles"),
                    ("03.1.7.10", "Cadre sup. des services touristiques et hôteliers"),
                    ("03.1.7.11", "Professions intermédiaires - cadres supérieurs non classés ailleurs"),
                ]
            ),
            (
                "03.1.8   Techniciens des sciences physiques et techniques",
                [
                    ("03.1.8.01", "Technicien chimiste"),
                    ("03.1.8.02", "Technicien de laboratoire"),
                    ("03.1.8.03", "Technicien géologue"),
                    ("03.1.8.04", "Technicien physicien"),
                    ("03.1.8.05", "Technicien géomètre"),
                    ("03.1.8.06", "Technicien météorologiste"),
                    ("03.1.8.07", "Technicien de génie civil"),
                    ("03.1.8.08", "Electrotechnicien"),
                    ("03.1.8.09", "Technicien électronicien"),
                    ("03.1.8.10", "Technicien des télécommunications"),
                    ("03.1.8.11", "Technicien frigoriste"),
                    ("03.1.8.12", "Technicien mécanicien"),
                    ("03.1.8.13", "Technicien métallurgiste"),
                    ("03.1.8.14", "Technicien, mines"),
                    ("03.1.8.15", "Dessinateur (industriel, génie civil, etc,)"),
                    ("03.1.8.16", "Assistant informatique"),
                    ("03.1.8.17", "Technicien, appareil audio-visuel"),
                    ("03.1.8.18", "Technicien appareil médical"),
                ]
            ),
            (
                "03.2.1   Cadres Moyens de l'Administration, du Travail et de la Sécurité Sociale",
                [
                    ("03.2.1.01", "Secrétaire de direction"),
                    ("03.2.1.02", "Secrétaire administratif"),
                    ("03.2.1.03", "Contrôleur de travail"),
                    ("03.2.1.04", "Assistant administratif"),
                ]
            ),
            (
                "03.2.2   Cadres Moyens de l'Enseignement et de la bibliothéconomie",
                [
                    ("03.2.2.01", "Maître, instituteur, enseignement primaire"),
                    ("03.2.2.02", "Maître, instituteur, enseignement préprimaire"),
                    ("03.2.2.03", "Jardinière d'enfants"),
                    ("03.2.2.04", "Moniteur, enseignement préprimaire"),
                    ("03.2.2.05", "Educateur spécialisés (aveugle, sourds, etc.)"),
                    ("03.2.2.06", "Assistant FJA (Formateur de Jeunes Agriculteurs)"),
                    ("03.2.2.07", "Surveillant de lycées et collèges"),
                    ("03.2.2.08", "Maître d'éducation physique et sportive - Educateur sportif"),
                    ("03.2.2.09", "Cadre moyen de la documentation"),
                ]
            ),
            (
                "03.2.3   Cadres Moyens de la Santé et de l'Action Sociale",
                [
                    ("03.2.3.01", "infirmier d'Etat spécialisé et breveté"),
                    ("03.2.3.02", "sage-femme d'Etat ou spécialisée"),
                    ("03.2.3.03", "Technicien et assistant d'assainissement"),
                    ("03.2.3.04", "Prothésiste dentaire"),
                    ("03.2.3.05", "Laborantin"),
                    ("03.2.3.06", "Gestionnaire des hôpitaux"),
                    ("03.2.3.07", "Aide sociale - éducateur social"),
                    ("03.2.3.08", "Puéricultrice"),
                    ("03.2.3.09", "Autre cadre moyen de santé et de l'action sociale"),
                ]
            ),
            (
                "03.2.4   Cadres Moyens des Télécommunications Transports Equipement - Bâtiments",
                [
                    ("03.2.4.01", "Chef de chantier"),
                    ("03.2.4.02", "Chef mécanicien"),
                    ("03.2.4.03", "Adjoint technique des T.P."),
                    ("03.2.4.04", "Contrôleur - receveur des P et T"),
                    ("03.2.4.05", "Assistant météorologiste et de la navigation aérienne"),
                    ("03.2.4.06", "Technicien du génie rural"),
                    ("03.2.4.07", "Contremaître"),
                ]
            ),
            (
                "03.2.5   Cadres Moyens des Ressources financières, Budget, Planification, commerce, banques et assurances",
                [
                    ("03.2.5.1", "Contrôleur des impôts"),
                    ("03.2.5.2", "Contrôleurs des douanes"),
                    ("03.2.5.3", "Contrôleur du trésor"),
                    ("03.2.5.4", "Percepteur"),
                    ("03.2.5.5", "Comptable"),
                    ("03.2.5.6", "Autres cadres moyens du budget, des ressources financières"),
                    ("03.2.5.7", "Assistant des affaires économiques et économe"),
                    ("03.2.5.8", "Assistant statisticien (adjoint technique de la statistique)"),
                    ("03.2.5.9", "Assistant, actuaire"),
                    ("03.2.5.10", "Assistant comptable"),
                ]
            ),
            (
                "03.2.6   Cadres Moyens de l'Agriculture, Elevage, Forêt, Géologie et Mines",
                [
                    ("03.2.6.01", "Technicien agronome"),
                    ("03.2.6.02", "Technicien forestier"),
                    ("03.2.6.03", "Assistant vétérinaire"),
                    ("03.2.6.04", "Conducteur des travaux agricoles"),
                    ("03.2.6.05", "agent technique d'agriculture spécialisé"),
                    ("03.2.6.06", "Contrôleurs des eaux et forêts"),
                    ("03.2.6.07", "Assistant et agent technique d'élevage spécialisé"),
                    ("03.2.6.08", "Technicien de la géologie et des mines"),
                ]
            ),
            (
                "03.2.7   Cadres Moyens de la Justice - de l'Information et des Affaires Etrangères",
                [
                    ("03.2.7.01", "Mandataire de justice"),
                    ("03.2.7.02", "Secrétaire des affaires étrangères"),
                    ("03.2.7.03", "Agent de maîtrise de l'information"),
                    ("03.2.7.04", "Reporter, speaker, animateur (radio et télévision)"),
                ]
            ),
            (
                "03.2.8   Cadres Moyens de la création artistique, du spectacle et des sports",
                [
                    ("03.2.8.01", "Arbitre, sport"),
                    ("03.2.8.02", "Entraîneur"),
                    ("03.2.8.03", "Moniteur sportif"),
                    ("03.2.8.04", "Athlète professionnel (coureur, footballeur, boxeur, etc,)"),
                    ("03.2.8.05", "Lutteur professionnel"),
                    ("03.2.8.06", "Jockey"),
                    ("03.2.8.07", "Moniteur, culture sportive"),
                ]
            ),
            (
                "03.2.9   Professions intermédiaires - cadre moyen NCA",
                [
                    ("03.2.9.01", "autres professions intermédiaires - cadre moyen NCA"),
                ]
            ),
            (
                "04.1.0   Cadres subalternes administration territoriale",
                [
                    ("04.1.0.01", "Agent de police"),
                ]
            ),
            (
                "04.2.0   Cadres subalternes de l'Agriculture - Elevage Forêt - Géologie et Mines",
                [
                    ("04.2.0.01", "Animateur rural"),
                    ("04.2.0.02", "Encadreur d'agriculture (Organisme de développement rural)"),
                    ("04.2.0.03", "Moniteur et formateur de jeunes agriculteurs (FJA)"),
                    ("04.2.0.04", "Préposé des eaux et forêt"),
                    ("04.2.0.05", "Agent technique d'agriculture et d'élevage"),
                    ("04.2.0.06", "Infirmier vétérinaire"),
                ]
            ),
            (
                "04.3.0   Cadres Subalternes des Administrations, Finances, Trésor, Planification, commerce, banque et assurances",
                [
                    ("04.3.0.01", "Employé de service administratif"),
                    ("04.3.0.02", "Adjoint administratif"),
                    ("04.3.0.03", "Aide- comptable"),
                    ("04.3.0.04", "Caissier, Guichetier"),
                    ("04.3.0.05", "Cadre subalterne du budget, et des ressources financières"),
                    ("04.3.0.06", "Agents administratif"),
                    ("04.3.0.07", "Agent de bureau (de recouvrement, des services fiscaux, de constatation d'assiette )"),
                    ("04.3.0.08", "Collecteur d'impôt"),
                    ("04.3.0.09", "Agent de douane, préposé des douanes"),
                    ("04.3.0.10", "Préposé, contrôle économique"),
                    ("04.3.0.11", "Cadre subalterne des affaires économiques - préposé des affaires économiques"),
                    ("04.3.0.12", "Secrétaire"),
                    ("04.3.0.13", "Dactylographe"),
                    ("04.3.0.14", "Standardiste - réceptionniste - téléphoniste"),
                    ("04.3.0.15", "planton - agent de liaison - commis d'administration"),
                    ("04.3.0.16", "relieur - reprographe"),
                    ("04.3.0.17", "agent et assistant technique de la statistique"),
                    ("04.3.0.18", "Agent de saisie, opérateur sur machine"),
                    ("04.3.0.19", "Agent de change"),
                    ("04.3.0.20", "Courtier, bourse"),
                    ("04.3.0.21", "Agent d'assurances"),
                    ("04.3.0.22", "Assureur"),
                    ("04.3.0.23", "Courtier, assurances"),
                    ("04.3.0.24", "Agent immobilier"),
                    ("04.3.0.25", "Courtier, immobilier"),
                    ("04.3.0.26", "Agent de voyages"),
                    ("04.3.0.27", "Agent commercial"),
                    ("04.3.0.28", "Démarcheur commercial"),
                    ("04.3.0.29", "Agent d'approvisionnement"),
                    ("04.3.0.30", "Commissaire-priseur"),
                ]
            ),
            (
                "04.4.O   Cadres Subalternes de l'Equipement - des Transports des Télécommunications - du Bâtiment",
                [
                    ("04.4.0.01", "Opérateur topographe"),
                    ("04.4.0.02", "Cheminot"),
                    ("04.4.0.03", "Opérateur du génie rural"),
                    ("04.4.0.04", "Agent de maîtrise de la géologie et des mines"),
                    ("04.4.0.05", "Cadre subalterne des transmissions météo"),
                    ("04.4.0.06", "Aide météo"),
                    ("04.4.0.07", "Cadre subalterne des P et T, facteur, opérateur des téléphones et télégraphes"),
                    ("04.4.0.08", "Surveillant des télécommunications"),
                ]
            ),
            (
                "04.5.0   Cadres Subalternes de la Santé",
                [
                    ("04.5.0.01", "Garçon ou fille de salle"),
                    ("04.5.0.02", "Agent itinérant de santé"),
                    ("04.5.0.03", "Distributeur de comprimés"),
                    ("04.5.0.04", "Aide infirmier - aide-soignant"),
                    ("04.5.0.05", "Accoucheuse auxiliaire - matrone"),
                    ("04.5.0.06", "Aide-laborantin"),
                    ("04.5.0.07", "Agent d'hygiène ; d'assainissement"),
                    ("04.5.0.08", "Autre personnel de santé subalterne"),
                ]
            ),
            (
                "04.6.0   Autre personnel subalterne",
                [
                    ("04.6.0.01", "Employé de bibliothèque, classeurs archivistes"),
                    ("04.6.0.02", "Employé d'approvisionnement"),
                    ("04.6.0.03", "Manoeuvre"),
                    ("04.6.0.04", "Ouvrier"),
                    ("04.6.0.05", "Magasinier"),
                    ("04.6.0.06", "Vérificateur"),
                    ("04.6.0.07", "Employé de bureau non classé ailleurs"),
                    ("04.6.0.08", "autre personnel du type administratif et cadre subalterne de l'administration NCA"),
                ]
            ),
            (
                "05.0.0   PERSONNEL DES SERVICES ET VENDEURS DE MAGASIN ET DE MARCHE",
                [
                    ("05.0.0.01", "Hôtesse, steward"),
                    ("05.0.0.02", "Chef de train"),
                    ("05.0.0.03", "Receveur (de train, du bus, etc.)"),
                    ("05.0.0.04", "Guide"),
                    ("05.0.0.05", "Boy-cuisinier, Gouvernante"),
                    ("05.0.0.06", "Chef de cuisine, cuisinier"),
                    ("05.0.0.07", "Pâtissier"),
                    ("05.0.0.08", "Boulanger"),
                    ("05.0.0.09", "Charcutier"),
                    ("05.0.0.10", "Poissonnier"),
                    ("05.0.0.11", "Presseur d'huile"),
                    ("05.0.0.12", "Barman"),
                    ("05.0.0.13", "maître et gérant d'hôtel"),
                    ("05.0.0.14", "serveur de restaurant - garçon d'hôtel"),
                    ("05.0.0.15", "propriétaires de restaurants"),
                    ("05.0.0.16", "servante de bar"),
                    ("05.0.0.17", "taxi man - conducteur de bus"),
                    ("05.0.0.18", "chauffeur"),
                    ("05.0.0.19", "coiffeur - coiffeuse"),
                    ("05.0.0.20", "Barbier"),
                    ("05.0.0.21", "laveur - nettoyeur"),
                    ("05.0.0.22", "Baby-sitter"),
                    ("05.0.0.23", "Astrologue, Diseur de bonne aventure"),
                    ("05.0.0.24", "Mannequins, modèles"),
                    ("05.0.0.25", "Garde de corp"),
                    ("05.0.0.26", "Détective, police privée"),
                    ("05.0.0.27", "Commis de magasin"),
                    ("05.0.0.28", "Pompiste"),
                    ("05.0.0.29", "Vendeur, établissement de commerce"),
                    ("05.0.0.30", "Commerçant (propriétaire, gérant de commerce de gros et de détail)"),
                    ("05.0.0.31", "boutiquier"),
                    ("05.0.0.32", "vendeur de tissus et friperie"),
                    ("05.0.0.33", "vendeur de fruits"),
                    ("05.0.0.34", "vendeur de céréales"),
                    ("05.0.0.35", "vendeur de vivres frais (alloco, igname, taro, autres féculents)"),
                    ("05.0.0.36", "vendeur de beignets et d'autres aliments préparés (vendeur d'aliments)"),
                    ("05.0.0.37", "vendeur de légumes et arachides et tous condiments"),
                    ("05.0.0.38", "aide vendeur"),
                    ("05.0.0.39", "conseiller commercial"),
                    ("05.0.0.40", "libraire"),
                    ("05.0.0.41", "boucher"),
                    ("05.0.0.42", "meunier"),
                    ("05.0.0.43", "Marchand de bois"),
                    ("05.0.0.44", "Gargotier/dibitier"),
                    ("05.0.0.45", "autres métiers de service et vendeurs NCA"),
                ]
            ),
            (
                "06.0.0   AGRICULTEURS ET OUVRIERS QUALIFIES DE L'AGRICULTURE ET LA PECHE",
                [
                    ("06.0.0.01", "Cultivateur"),
                    ("06.0.0.02", "maraîcher"),
                    ("06.0.0.03", "jardinier"),
                    ("06.0.0.04", "exploitant de verger - pépiniériste"),
                    ("06.0.0.05", "Exploitant forestier"),
                    ("06.0.0.06", "bûcheron"),
                    ("06.0.0.07", "éleveur de bétail"),
                    ("06.0.0.08", "éleveur de volaille"),
                    ("06.0.0.09", "berger - garde-animaux"),
                    ("06.0.0.10", "pêcheur"),
                    ("06.0.0.11", "marin pêcheur"),
                    ("06.0.0.12", "chasseur"),
                    ("06.0.0.13", "Apiculteur"),
                    ("06.0.0.14", "sériciculteur"),
                    ("06.0.0.15", "pisciculteur"),
                    ("06.0.0.16", "charbonnier"),
                    ("06.0.0.17", "ouvrier qualifié de l'agriculture"),
                    ("06.0.0.18", "autres métiers de ce groupe non classés ailleurs"),
                ]
            ),
            (
                "07.0.0   ARTISANS ET OUVRIERS DES METIERS DE TYPE ARTISANAL",
                [
                    ("07.0.0.01", "Mineur"),
                    ("07.0.0.02", "Foreur de puits"),
                    ("07.0.0.03", "Carrier"),
                    ("07.0.0.04", "Tailleur de pierre"),
                    ("07.0.0.05", "Marbrier"),
                    ("07.0.0.06", "Creuseur de puits"),
                    ("07.0.0.07", "maçon - tâcheron"),
                    ("07.0.0.08", "entrepreneur"),
                    ("07.0.0.09", "Ferrailleur"),
                    ("07.0.0.10", "Echaffaudeur"),
                    ("07.0.0.11", "Charpentier"),
                    ("07.0.0.12", "Carreleur, poseur revêtement de sol"),
                    ("07.0.0.13", "Plafonneur"),
                    ("07.0.0.14", "Plâtrier"),
                    ("07.0.0.15", "Vitrier"),
                    ("07.0.0.16", "Plombier"),
                    ("07.0.0.17", "Puisatier"),
                    ("07.0.0.18", "Electricien"),
                    ("07.0.0.19", "Peintre en bâtiment"),
                    ("07.0.0.20", "Peintre, carrosserie"),
                    ("07.0.0.21", "Soudeur"),
                    ("07.0.0.22", "Chaudronnier"),
                    ("07.0.0.23", "Ferblantier"),
                    ("07.0.0.24", "Tôlier"),
                    ("07.0.0.25", "Forgeron"),
                    ("07.0.0.26", "Armurier"),
                    ("07.0.0.27", "Serrurier"),
                    ("07.0.0.28", "Mécanicien, garagiste"),
                    ("07.0.0.29", "Mécanicien, réparateur de petit engin"),
                    ("07.0.0.30", "Electromécanicien"),
                    ("07.0.0.31", "Dépanneur : récepteur radio et télévision"),
                    ("07.0.0.32", "Bijoutier, joaillier, orfèvre"),
                    ("07.0.0.33", "Potier"),
                    ("07.0.0.34", "Menuisier, Ebéniste, artisan article en bois"),
                    ("07.0.0.35", "Vannier / artisan tressage de corbeille"),
                    ("07.0.0.36", "Tailleur / brodeur"),
                    ("07.0.0.37", "Tisserand"),
                    ("07.0.0.38", "Tricoteur"),
                    ("07.0.0.39", "Teinturier / artisan du textile"),
                    ("07.0.0.40", "Imprimeur"),
                    ("07.0.0.41", "Boucher"),
                    ("07.0.0.42", "Matelassier"),
                    ("07.0.0.43", "Tapissier"),
                    ("07.0.0.44", "Tanneur"),
                    ("07.0.0.45", "Cordonnier"),
                    ("07.0.0.46", "Maroquinier"),
                    ("07.0.0.47", "Réparateur de chaussures"),
                    ("07.0.0.48", "dolotière"),
                    ("07.0.0.49", "fileuse de coton"),
                    ("07.0.0.50", "réparateur de montre - horloger"),
                    ("07.0.0.51", "autres métiers de ce groupe non classé ailleurs"),
                ]
            ),
            (
                "08.0.0   CONDUCTEUR D'INSTALLATIONS ET DE MACHINES ET OUVRIERS DE L'ASSEMBLAGE",
                [
                    ("08.0.0.01", "Conducteur de machine et installation fixe"),
                    ("08.0.0.02", "Conducteur de train, locomotive"),
                    ("08.0.0.03", "Coursier (cycliste, motocyclette)"),
                    ("08.0.0.04", "Conducteur d'autobus et d'autocar"),
                    ("08.0.0.05", "Conducteur de camion (citerne, remorque)"),
                    ("08.0.0.06", "Conducteur d'engin agricole et forestier"),
                    ("08.0.0.07", "Conducteur d'engins de chantier"),
                    ("08.0.0.08", "Batelier"),
                    ("08.0.0.09", "Matelot"),
                    ("08.0.0.10", "Monteur"),
                    ("08.0.0.11", "autres métiers de ce groupe non classé ailleurs"),
                ]
            ),
            (
                "09.0.0   OUVRIERS ET EMPLOYES NON QUALIFIES",
                [
                    ("09.0.0.01", "Marchand ambulant"),
                    ("09.0.0.02", "Colporteur"),
                    ("09.0.0.03", "Vendeur de journaux"),
                    ("09.0.0.04", "Livreur, distributeur"),
                    ("09.0.0.05", "Cireur de chaussure"),
                    ("09.0.0.06", "Garçons de courses"),
                    ("09.0.0.07", "Laveur ambulant (vitre de voiture)"),
                    ("09.0.0.08", "Domestique, bonne, aide ménagère"),
                    ("09.0.0.09", "Nettoyeur"),
                    ("09.0.0.10", "Plongeur"),
                    ("09.0.0.11", "Blanchisseur"),
                    ("09.0.0.12", "Concierge"),
                    ("09.0.0.13", "Gardien - veilleur de nuit"),
                    ("09.0.0.14", "Eboueur"),
                    ("09.0.0.15", "Balayeur"),
                    ("09.0.0.16", "Ouvrier, manœuvre agricole"),
                    ("09.0.0.17", "Manœuvre en bâtiment"),
                    ("09.0.0.18", "Charretier"),
                    ("09.0.0.19", "Docker"),
                    ("09.0.0.20", "autres métiers de ce groupe non classé ailleurs"),
                ]
            ),
            (
                "10.0.0   ARMEE, SECURITE ET AUTRES METIERS",
                [
                    ("10.0.0.01", "militaire"),
                    ("10.0.0.02", "gendarme"),
                    ("10.0.0.03", "pompier"),
                    ("10.0.0.04", "agent de la garde nationale"),
                    ("10.0.0.05", "autre personnel de l'armée et de la sécurité"),
                    ("10.0.0.06", "autres professions non classées ailleurs"),
                ]
            ),
        ]
        
        # Liste des nouvelles fonctions à intégrer
        # Vous devez décider dans quel domaine les placer
        liste_nouvelles_fonctions = [
            # Format: (code, libelle, code_domaine_parent)
            # Exemple: ("99.0.0.01", "Nouvelle fonction 1", "10.0.0"),
            # Vous devez spécifier le code_domaine_parent pour chaque fonction
        ]
        
        # Vérification des doublons dans les données source
        if not dry_run:
            self.verify_source_data(post_total_data)
        
        if dry_run:
            self.stdout.write("[WARNING] " + "DRY RUN MODE - No data will be saved")
            self.simulate_import(post_total_data, liste_nouvelles_fonctions, clear_data, skip_domaines, skip_postes)
            return
        
        try:
            with transaction.atomic():
                # Étape 1: Vider les données existantes si demandé
                if clear_data:
                    self.clear_existing_data(skip_domaines, skip_postes)
                
                # Étape 2: Importer les domaines et postes
                stats = self.import_data(post_total_data, liste_nouvelles_fonctions, skip_domaines, skip_postes)
                
                self.stdout.write("[SUCCESS] " + 'Successfully imported Domaines et Postes data!')
                self.print_stats(stats)
                
                # Étape 3: Vérifier l'intégrité
                self.verify_database_integrity()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
    
    def verify_source_data(self, post_total_data):
        """Vérifie les doublons dans les données source"""
        domaine_codes = set()
        poste_codes = set()
        duplicates_domaines = []
        duplicates_postes = []
        
        for domaine_libelle, postes in post_total_data:
            # Extraire le code du domaine (première partie avant les espaces)
            parts = domaine_libelle.strip().split()
            if parts:
                domaine_code = parts[0]
                if domaine_code in domaine_codes:
                    duplicates_domaines.append(domaine_code)
                else:
                    domaine_codes.add(domaine_code)
            
            # Vérifier les codes de postes
            for poste_code, _ in postes:
                if poste_code in poste_codes:
                    duplicates_postes.append(poste_code)
                else:
                    poste_codes.add(poste_code)
        
        if duplicates_domaines:
            self.stdout.write(self.style.WARNING(f"Duplicate domain codes in source: {set(duplicates_domaines)}"))
        
        if duplicates_postes:
            self.stdout.write(self.style.WARNING(f"Duplicate poste codes in source: {set(duplicates_postes)}"))
        
        return len(duplicates_domaines) == 0 and len(duplicates_postes) == 0
    
    def clear_existing_data(self, skip_domaines, skip_postes):
        """Vide les données existantes"""
        if not skip_postes:
            self.stdout.write("[WARNING] " + 'Clearing existing PosteEntreprise data...')
            postes_count = PosteEntreprise.objects.count()
            PosteEntreprise.objects.all().delete()
            self.stdout.write("[SUCCESS] " + f'Cleared {postes_count} postes.')
        
        if not skip_domaines:
            # Les domaines doivent être supprimés après les postes (dépendances)
            self.stdout.write("[WARNING] " + 'Clearing existing DomaineEntreprise data...')
            domaines_count = DomaineEntreprise.objects.count()
            DomaineEntreprise.objects.all().delete()
            self.stdout.write("[SUCCESS] " + f'Cleared {domaines_count} domaines.')
    
    def extract_domaine_info(self, domaine_libelle):
        """Extrait le code et libellé nettoyé du domaine"""
        # Le format est: "01.1.0   MEMBRES DE L'EXECUTIF ET DU CORPS LEGISLATIF"
        parts = domaine_libelle.strip().split(maxsplit=1)
        if len(parts) == 2:
            code = parts[0].strip()
            libelle_complet = parts[1].strip()
            # Convertir en minuscules (sauf acronymes peut-être)
            libelle_minuscule = libelle_complet.lower()
            return code, libelle_minuscule, libelle_complet
        else:
            # Fallback si pas d'espace
            return domaine_libelle.strip(), domaine_libelle.strip().lower(), domaine_libelle.strip()
    
    def extract_poste_info(self, poste_code, poste_libelle):
        """Extrait le code et libellé nettoyé du poste"""
        # Le format est: "01.1.0.01    Président de la république"
        code = poste_code.strip()
        # Nettoyer le libellé (supprimer le code au début si présent)
        libelle_brut = poste_libelle.strip()
        if libelle_brut.startswith(code):
            libelle = libelle_brut[len(code):].strip()
        else:
            libelle = libelle_brut
        return code, libelle.lower(), libelle_brut
    
    def import_data(self, post_total_data, liste_nouvelles_fonctions, skip_domaines, skip_postes):
        """Importe les domaines et postes"""
        stats = {
            'domaines_created': 0,
            'domaines_updated': 0,
            'postes_created': 0,
            'postes_updated': 0,
            'postes_skipped': 0,
            'errors': 0,
        }
        
        # Dictionnaire pour mapper les codes de domaine aux objets
        domaine_map = {}
        
        self.stdout.write("Starting import...")
        
        # 1. Importer les domaines
        if not skip_domaines:
            self.stdout.write("\n=== IMPORTING DOMAINES ===")
            for i, (domaine_libelle, postes) in enumerate(post_total_data, 1):
                try:
                    code, libelle_minuscule, libelle_complet = self.extract_domaine_info(domaine_libelle)
                    
                    # Créer ou mettre à jour le domaine
                    domaine, created = DomaineEntreprise.objects.update_or_create(
                        code=code,
                        defaults={
                            'libelle': libelle_minuscule,
                            'active': True,
                            'description': f"Domaine: {libelle_complet}",
                        }
                    )
                    
                    domaine_map[code] = domaine
                    
                    if created:
                        stats['domaines_created'] += 1
                        self.stdout.write("[SUCCESS] " + f'  [OK] Domaine créé: {code} - {libelle_minuscule}')
                    else:
                        stats['domaines_updated'] += 1
                        self.stdout.write("[WARNING] " + f'  [UPD] Domaine mis à jour: {code} - {libelle_minuscule}')
                    
                    # Afficher la progression
                    if i % 10 == 0:
                        self.stdout.write(f"  Processed {i}/{len(post_total_data)} domaines...")
                        
                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Error importing domaine {domaine_libelle}: {str(e)}'))
        
        # 2. Importer les postes
        if not skip_postes:
            self.stdout.write("\n=== IMPORTING POSTES ===")
            total_postes = sum(len(postes) for _, postes in post_total_data)
            poste_counter = 0
            
            for domaine_libelle, postes in post_total_data:
                domaine_code, _, _ = self.extract_domaine_info(domaine_libelle)
                domaine = domaine_map.get(domaine_code)
                
                if not domaine:
                    self.stdout.write("[ERROR] " + f"  Domaine {domaine_code} not found for postes")
                    continue
                
                for poste_code, poste_libelle in postes:
                    poste_counter += 1
                    try:
                        code, libelle_minuscule, libelle_complet = self.extract_poste_info(poste_code, poste_libelle)
                        
                        # Créer ou mettre à jour le poste
                        poste, created = PosteEntreprise.objects.update_or_create(
                            code=code,
                            defaults={
                                'domaine': domaine,
                                'libelle': libelle_minuscule,
                                'active': True,
                                'description': f"Poste: {libelle_complet}",
                            }
                        )
                        
                        if created:
                            stats['postes_created'] += 1
                            if poste_counter % 50 == 0 or poste_counter <= 10:
                                self.stdout.write(f'    [OK] Poste créé: {code} - {libelle_minuscule}')
                        else:
                            stats['postes_updated'] += 1
                            if poste_counter % 100 == 0:
                                self.stdout.write(f'    [UPD] Poste mis à jour: {code}')
                        
                        # Afficher la progression
                        if poste_counter % 100 == 0:
                            self.stdout.write(f"    Processed {poste_counter}/{total_postes} postes...")
                            
                    except Exception as e:
                        stats['errors'] += 1
                        if poste_counter % 20 == 0:  # Afficher moins fréquemment les erreurs
                            self.stdout.write(self.style.ERROR(f'    ✗ Error importing poste {poste_code}: {str(e)}'))
            
            # 3. Importer les nouvelles fonctions (si spécifiées)
            if liste_nouvelles_fonctions:
                self.stdout.write("\n=== IMPORTING NOUVELLES FONCTIONS ===")
                for code, libelle, domaine_parent_code in liste_nouvelles_fonctions:
                    try:
                        domaine_parent = domaine_map.get(domaine_parent_code)
                        if not domaine_parent:
                            self.stdout.write("[WARNING] " + f"  Domaine parent {domaine_parent_code} not found for {code}")
                            continue
                        
                        poste, created = PosteEntreprise.objects.update_or_create(
                            code=code,
                            defaults={
                                'domaine': domaine_parent,
                                'libelle': libelle.lower(),
                                'active': True,
                                'description': f"Nouvelle fonction: {libelle}",
                            }
                        )
                        
                        if created:
                            stats['postes_created'] += 1
                            self.stdout.write("[SUCCESS] " + f'  [OK] Nouvelle fonction créée: {code} - {libelle}')
                        else:
                            stats['postes_updated'] += 1
                            self.stdout.write("[WARNING] " + f'  [UPD] Nouvelle fonction mise à jour: {code} - {libelle}')
                            
                    except Exception as e:
                        stats['errors'] += 1
                        self.stdout.write(self.style.ERROR(f'  ✗ Error importing nouvelle fonction {code}: {str(e)}'))
        
        return stats
    
    def simulate_import(self, post_total_data, liste_nouvelles_fonctions, clear_data, skip_domaines, skip_postes):
        """Simule l'importation"""
        self.stdout.write("="*70)
        self.stdout.write("DRY RUN - SIMULATION ONLY")
        self.stdout.write("="*70)
        
        if clear_data:
            if not skip_postes:
                self.stdout.write("[WARNING] " + "Would clear all PosteEntreprise data")
            if not skip_domaines:
                self.stdout.write("[WARNING] " + "Would clear all DomaineEntreprise data")
        
        # Compter les données
        total_domaines = len(post_total_data)
        total_postes = sum(len(postes) for _, postes in post_total_data)
        total_nouvelles = len(liste_nouvelles_fonctions)
        
        self.stdout.write(f"\n[STATS] SOURCE DATA SUMMARY:")
        self.stdout.write(f"  Domaines à importer: {total_domaines}")
        self.stdout.write(f"  Postes à importer: {total_postes}")
        self.stdout.write(f"  Nouvelles fonctions: {total_nouvelles}")
        
        if not skip_domaines:
            self.stdout.write("\n[NEW] DOMAINES (en minuscules):")
            for i, (domaine_libelle, _) in enumerate(post_total_data[:5], 1):  # Afficher 5 premiers
                code, libelle_minuscule, _ = self.extract_domaine_info(domaine_libelle)
                self.stdout.write(f"  {i}. {code} → '{libelle_minuscule}'")
            if total_domaines > 5:
                self.stdout.write(f"  ... et {total_domaines - 5} autres")
        
        if not skip_postes:
            self.stdout.write("\n[NEW] POSTES (en minuscules - exemple):")
            # Afficher quelques exemples
            for domaine_libelle, postes in post_total_data[:2]:  # 2 premiers domaines
                code_dom, lib_dom, _ = self.extract_domaine_info(domaine_libelle)
                self.stdout.write(f"\n  Domaine: {code_dom} - {lib_dom}")
                for poste_code, poste_libelle in postes[:3]:  # 3 premiers postes
                    code_post, lib_post, _ = self.extract_poste_info(poste_code, poste_libelle)
                    self.stdout.write(f"    - {code_post} → '{lib_post}'")
        
        # Vérifier les doublons
        self.stdout.write("\n[SEARCH] CHECKING FOR DUPLICATES...")
        if self.verify_source_data(post_total_data):
            self.stdout.write("[SUCCESS] " + "[OK] No duplicates found in source data")
        else:
            self.stdout.write("[WARNING] " + "[WARN] Possible duplicates in source data")
        
        self.stdout.write("="*70)
    
    def verify_database_integrity(self):
        """Vérifie l'intégrité de la base de données"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("DATABASE INTEGRITY CHECK")
        self.stdout.write("="*50)
        
        # Compter
        total_domaines = DomaineEntreprise.objects.count()
        total_postes = PosteEntreprise.objects.count()
        postes_sans_domaine = PosteEntreprise.objects.filter(domaine__isnull=True).count()
        domaines_sans_postes = DomaineEntreprise.objects.filter(postes__isnull=True).count()
        domaines_inactifs = DomaineEntreprise.objects.filter(active=False).count()
        postes_inactifs = PosteEntreprise.objects.filter(active=False).count()
        
        self.stdout.write(f"Total domaines: {total_domaines}")
        self.stdout.write(f"Total postes: {total_postes}")
        
        if postes_sans_domaine > 0:
            self.stdout.write("[ERROR] " + f"Postes sans domaine: {postes_sans_domaine}")
        else:
            self.stdout.write("[SUCCESS] " + "[OK] Tous les postes ont un domaine")
        
        if domaines_sans_postes > 0:
            self.stdout.write("[WARNING] " + f"Domaines sans postes: {domaines_sans_postes}")
        
        if domaines_inactifs > 0:
            self.stdout.write(f"Domaines inactifs: {domaines_inactifs}")
        
        if postes_inactifs > 0:
            self.stdout.write(f"Postes inactifs: {postes_inactifs}")
        
        # Vérifier les codes uniques
        codes_duplicates = self.check_duplicate_codes()
        if codes_duplicates:
            self.stdout.write("[ERROR] " + f"Codes en double: {codes_duplicates}")
        else:
            self.stdout.write("[SUCCESS] " + "[OK] Tous les codes sont uniques")
        
        self.stdout.write("="*50)
    
    def check_duplicate_codes(self):
        """Vérifie les codes en double"""
        from django.db.models import Count
        
        # Vérifier les domaines
        domaines_dups = DomaineEntreprise.objects.values('code').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        # Vérifier les postes
        postes_dups = PosteEntreprise.objects.values('code').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        duplicates = []
        if domaines_dups:
            duplicates.append(f"Domaines: {[d['code'] for d in domaines_dups]}")
        if postes_dups:
            duplicates.append(f"Postes: {[p['code'] for p in postes_dups]}")
        
        return ", ".join(duplicates) if duplicates else None
    
    def print_stats(self, stats):
        """Affiche les statistiques"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT STATISTICS")
        self.stdout.write("="*50)
        
        if 'domaines_created' in stats:
            self.stdout.write(f"Domaines créés: {stats['domaines_created']}")
            self.stdout.write(f"Domaines mis à jour: {stats['domaines_updated']}")
        
        if 'postes_created' in stats:
            self.stdout.write(f"Postes créés: {stats['postes_created']}")
            self.stdout.write(f"Postes mis à jour: {stats['postes_updated']}")
            self.stdout.write(f"Postes ignorés (doublons): {stats.get('postes_skipped', 0)}")
        
        self.stdout.write(f"Erreurs: {stats['errors']}")
        
        # Vérifier la cohérence
        total_in_db_domaines = DomaineEntreprise.objects.count()
        total_in_db_postes = PosteEntreprise.objects.count()
        
        self.stdout.write(f"\nTotal domaines en base: {total_in_db_domaines}")
        self.stdout.write(f"Total postes en base: {total_in_db_postes}")
        
        self.stdout.write("="*50)


# Version optimisée avec bulk_create pour les grandes quantités
class CommandBulk(BaseCommand):
    help = 'Import Domaines et Postes (version optimisée)'
    
    def handle(self, *args, **options):
        # Vous devez transformer vos données POST_TOTAL en format plat
        # Cette version est plus rapide mais nécessite plus de mémoire
        
        post_total_data = [
            # Même format que précédemment
        ]
        
        try:
            with transaction.atomic():
                # 1. Créer tous les domaines
                domaines_a_creer = []
                domaine_map = {}
                
                for domaine_libelle, _ in post_total_data:
                    parts = domaine_libelle.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        code = parts[0].strip()
                        libelle = parts[1].strip().lower()
                        
                        domaines_a_creer.append(
                            DomaineEntreprise(
                                code=code,
                                libelle=libelle,
                                active=True,
                                description=f"Domaine: {parts[1].strip()}",
                            )
                        )
                
                # Bulk create domaines
                created_domaines = DomaineEntreprise.objects.bulk_create(
                    domaines_a_creer,
                    ignore_conflicts=False
                )
                
                # Récupérer les domaines créés
                for domaine in DomaineEntreprise.objects.all():
                    domaine_map[domaine.code] = domaine
                
                self.stdout.write(f"[OK] {len(created_domaines)} domaines créés")
                
                # 2. Créer tous les postes
                postes_a_creer = []
                
                for domaine_libelle, postes in post_total_data:
                    parts = domaine_libelle.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        domaine_code = parts[0].strip()
                        domaine = domaine_map.get(domaine_code)
                        
                        if domaine:
                            for poste_code, poste_libelle in postes:
                                # Nettoyer le libellé du poste
                                libelle_brut = poste_libelle.strip()
                                if libelle_brut.startswith(poste_code.strip()):
                                    libelle = libelle_brut[len(poste_code.strip()):].strip().lower()
                                else:
                                    libelle = libelle_brut.lower()
                                
                                postes_a_creer.append(
                                    PosteEntreprise(
                                        domaine=domaine,
                                        code=poste_code.strip(),
                                        libelle=libelle,
                                        active=True,
                                        description=f"Poste: {libelle_brut}",
                                    )
                                )
                
                # Bulk create postes
                created_postes = PosteEntreprise.objects.bulk_create(
                    postes_a_creer,
                    ignore_conflicts=False
                )
                
                self.stdout.write(f"[OK] {len(created_postes)} postes créés")
                self.stdout.write("[SUCCESS] " + '\nImport terminé avec succès!')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
        
        
        
        




# Import complet
# python manage.py import_domaines_poste_entreprise --clear

# Test (dry run)
# python manage.py import_domaines_poste_entreprise --dry-run --clear

# Importer seulement les domaines
# python manage.py import_domaines_poste_entreprise --clear --skip-postes

# Importer seulement les postes (domaines doivent exister)
# python manage.py import_domaines_poste_entreprise --skip-domaines