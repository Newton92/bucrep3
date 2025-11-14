import json
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from weasyprint import HTML
from main.models import *
from main.serializers_solvency_reporting import ReportSolvabiliteCompletSerializer
import json
import os
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

class ReportGenerator:
    def __init__(self, acheteur_id, language='fr', devise='XAF', bilan_type='Classique', commande_id=None):
        self.acheteur_id = acheteur_id
        self.language = language
        self.devise = devise
        self.bilan_type = bilan_type
        self.commande_id = commande_id
        self.acheteur = None
        self.data = {}
        
    def collect_data(self):
        """Collecte toutes les données nécessaires pour le rapport"""
        try:
            self.acheteur = Acheteur.objects.get(id=self.acheteur_id)
            
            self.data = {
                'acheteur': self.acheteur,
                'resume': Resume.objects.filter(acheteur=self.acheteur).first(),
                'risk_rating': RiskRating.objects.filter(acheteur=self.acheteur).first(),
                'donnees_enregistrement': DonneesEnregistrement.objects.filter(acheteur=self.acheteur).first(),
                'antecedants_juridiques': AntecedantsJuridique.objects.filter(acheteur=self.acheteur).first(),
                'responsables': ResponsableAcheteur.objects.filter(acheteur=self.acheteur),
                'risk_management': RiskManagment.objects.filter(acheteur=self.acheteur).first(),
                'capital_social': CompositionCapitalSocial.objects.filter(acheteur=self.acheteur).first(),
                'actionnaires': CompositionAction.objects.filter(acheteur=self.acheteur),
                'structures': Structure.objects.filter(acheteur=self.acheteur),
                'analyse_sectorielle': AnalyseSectorielle.objects.filter(acheteur=self.acheteur).first(),
                'tendance': Tendance.objects.filter(acheteur=self.acheteur).first(),
                'geopolitics': Geopolitics.objects.filter(acheteur=self.acheteur).first(),
                'banquiers': Banquier.objects.filter(acheteur=self.acheteur),
                'compte_financier': CompteFinancier.objects.filter(acheteur=self.acheteur).first(),
                'operation_historique': OperationEtHistorique.objects.filter(acheteur=self.acheteur).first(),
                'proprietes_actifs': ProprieteEtActif.objects.filter(acheteur=self.acheteur),
                'conditions_achat': ConditionAchat.objects.filter(acheteur=self.acheteur).first(),
                'conditions_vente': ConditionDeVente.objects.filter(acheteur=self.acheteur).first(),
                'sommaire_avis': SommaireEtAvis.objects.filter(acheteur=self.acheteur).first(),
                'advice': Advice.objects.filter(acheteur=self.acheteur).first(),
                'scoring_sans_bilan': ScoringSansBilanAcheteur.objects.filter(acheteur=self.acheteur).first(),
            }
            
            # Récupérer les données de bilan selon le type sélectionné
            self.data['bilan_data'] = self._get_bilan_data()
            self.data['ratios_data'] = self._calculate_ratios()
            
            return True
            
        except Acheteur.DoesNotExist:
            return False
    
    def _get_bilan_data(self):
        """Récupère les données de bilan selon le type sélectionné"""
        bilan_data = {}
        
        if self.bilan_type == 'Classique':
            # Récupérer les 3 dernières années de bilans classiques
            actifs = ActifC.objects.filter(acheteur=self.acheteur).order_by('-annee__annee')[:3]
            passifs = PassifC.objects.filter(acheteur=self.acheteur).order_by('-annee__annee')[:3]
            resultats = ResultatC.objects.filter(acheteur=self.acheteur).order_by('-annee__annee')[:3]
            
            bilan_data = {
                'type': 'Classique',
                'actifs': actifs,
                'passifs': passifs,
                'resultats': resultats
            }
            
        elif self.bilan_type == 'Anglais':
            # Implémentation similaire pour le bilan anglais
            pass
            
        elif self.bilan_type == 'Syscohada':
            # Implémentation similaire pour SYSCOHADA
            pass
            
        elif self.bilan_type == 'Bancaire':
            # Implémentation similaire pour bancaire
            pass
            
        elif self.bilan_type == 'IFRS COBAC':
            # Implémentation similaire pour IFRS
            pass
            
        return bilan_data
    
    def _calculate_ratios(self):
        """Calcule les ratios financiers"""
        ratios = {}
        
        # Implémentation des calculs de ratios selon le type de bilan
        # Cette partie peut être étendue selon les besoins
        
        return ratios
    
    def _convert_currency(self, amount, from_currency, to_currency):
        """Convertit un montant d'une devise à une autre"""
        # Taux de change fictifs - à remplacer par une API réelle
        exchange_rates = {
            'XAF': {'USD': 0.0016, 'EUR': 0.0015, 'XOF': 1.0},
            'USD': {'XAF': 600.0, 'EUR': 0.85, 'XOF': 600.0},
            'EUR': {'XAF': 655.0, 'USD': 1.18, 'XOF': 655.0},
            'XOF': {'XAF': 1.0, 'USD': 0.0016, 'EUR': 0.0015}
        }
        
        if from_currency == to_currency:
            return amount
            
        if from_currency in exchange_rates and to_currency in exchange_rates[from_currency]:
            rate = exchange_rates[from_currency][to_currency]
            return amount * Decimal(rate)
            
        return amount
    
    def generate_pdf(self):
        """Génère le rapport en format PDF"""
        if not self.collect_data():
            return None
            
        context = {
            'data': self.data,
            'language': self.language,
            'devise': self.devise,
            'bilan_type': self.bilan_type,
            'commande_id': self.commande_id
        }
        
        html_string = render_to_string('reports/solvability_report_fr.html', context)
        html = HTML(string=html_string, base_url='.')
        pdf = html.write_pdf()
        
        return pdf
    
    def generate_html(self):
        """Génère le rapport en format HTML"""
        if not self.collect_data():
            return None
            
        context = {
            'data': self.data,
            'language': self.language,
            'devise': self.devise,
            'bilan_type': self.bilan_type,
            'commande_id': self.commande_id
        }
        
        template_name = f'reports/solvability_report_{self.language}.html'
        html = render_to_string(template_name, context)
        
        return html
    
    def generate_json(self):
        """Génère le rapport en format JSON"""
        if not self.collect_data():
            return None
            
        serializer = ReportSolvabiliteCompletSerializer(self.data)
        return json.dumps(serializer.data, indent=2, ensure_ascii=False)
    
    def generate_xml(self):
        """Génère le rapport en format XML"""
        if not self.collect_data():
            return None
            
        # Implémentation basique de génération XML
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_parts.append('<rapport_solvabilite>')
        
        # Ajouter les données de base
        xml_parts.append(f'<acheteur><nom>{self.acheteur.nom}</nom></acheteur>')
        
        # Ajouter d'autres sections...
        
        xml_parts.append('</rapport_solvabilite>')
        
        return '\n'.join(xml_parts)
    
    
    
    

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([])  # Ajoutez cette ligne
def generer_rapport_solvabilite(request, acheteur_id):
    """
    Endpoint principal pour générer les rapports de solvabilité
    """
    # Vérifier que l'utilisateur a accès à cet acheteur
    try:
        acheteur = Acheteur.objects.get(id=acheteur_id)
        # Ici vous pouvez ajouter une logique de permission spécifique
        # par exemple vérifier si l'utilisateur fait partie du client lié à l'acheteur
    except Acheteur.DoesNotExist:
        return Response({'error': 'Acheteur non trouvé'}, status=404)
    
    # Le reste du code reste inchangé...
    commande_id = request.GET.get('id_commande')
    language = request.GET.get('language', 'fr')
    devise = request.GET.get('devise', 'XAF')
    bilan_type = request.GET.get('bilan_report', 'Classique')
    format_report = request.GET.get('format_report', 'pdf')
    
    # Validation des paramètres
    valid_languages = ['fr', 'en']
    valid_devises = ['XAF', 'XOF', 'USD', 'EUR', 'GBP', 'JPY']
    valid_bilan_types = ['Classique', 'Anglais', 'Syscohada', 'Bancaire', 'IFRS COBAC']
    valid_formats = ['pdf', 'html', 'json', 'xml']
    
    if language not in valid_languages:
        return Response({'error': 'Langue non supportée'}, status=400)
    if devise not in valid_devises:
        return Response({'error': 'Devise non supportée'}, status=400)
    if bilan_type not in valid_bilan_types:
        return Response({'error': 'Type de bilan non supporté'}, status=400)
    if format_report not in valid_formats:
        return Response({'error': 'Format non supporté'}, status=400)
    
    # Génération du rapport
    generator = ReportGenerator(
        acheteur_id=acheteur_id,
        language=language,
        devise=devise,
        bilan_type=bilan_type,
        commande_id=commande_id
    )
    
    try:
        if format_report == 'pdf':
            pdf_content = generator.generate_pdf()
            if pdf_content:
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="rapport_solvabilite_{acheteur_id}.pdf"'
                return response
            else:
                return Response({'error': 'Erreur lors de la génération du PDF'}, status=500)
                
        elif format_report == 'html':
            html_content = generator.generate_html()
            if html_content:
                return HttpResponse(html_content, content_type='text/html')
            else:
                return Response({'error': 'Erreur lors de la génération du HTML'}, status=500)
                
        elif format_report == 'json':
            json_content = generator.generate_json()
            if json_content:
                return JsonResponse(json.loads(json_content), safe=False, json_dumps_params={'ensure_ascii': False})
            else:
                return Response({'error': 'Erreur lors de la génération du JSON'}, status=500)
                
        elif format_report == 'xml':
            xml_content = generator.generate_xml()
            if xml_content:
                return HttpResponse(xml_content, content_type='application/xml')
            else:
                return Response({'error': 'Erreur lors de la génération du XML'}, status=500)
                
    except Exception as e:
        import traceback
        print(f"Erreur détaillée: {traceback.format_exc()}")
        return Response({'error': f'Erreur lors de la génération: {str(e)}'}, status=500)
    
    return Response({'error': 'Format non implémenté'}, status=501)