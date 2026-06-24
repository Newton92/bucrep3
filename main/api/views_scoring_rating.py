# views_scoring_rating.py — Score / Rating ACREMAC basé sur états financiers

import logging
from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from main.models import Acheteur, ActifC, PassifC, ResultatC, Annee, ScoringRating
from main.serializers import UserSimpleSerializer

logger = logging.getLogger(__name__)


# ======================================================================
#  Service de calcul
# ======================================================================
class ScoringRatingService:
    """
    Calcule le Score/Rating ACREMAC basé sur 7 critères pondérés.
    Total des pondérations = 100%.
    """
    COEFFICIENTS = {
        'solvabilite':         0.15,   # Financier
        'ebitda':              0.15,   # Financier
        'liquidite':           0.10,   # Financier
        'historique_paiement': 0.20,   # Comportemental — Red Flag si = 0
        'anciennete':          0.10,   # Comportemental — auto
        'secteur_activite':    0.15,   # Qualitatif
        'management':          0.15,   # Qualitatif
    }

    # -- Bornes de normalisation ----------------------------------------
    # Solvabilité (FP / Total bilan) : ≥40% → 10 / ≤10% → 0
    BORNE_SOLV_MIN, BORNE_SOLV_MAX = 0.10, 0.40
    # EBITDA (EBE / CA) : ≥25% → 10 / ≤0% → 0
    BORNE_EBITDA_MIN, BORNE_EBITDA_MAX = 0.0, 0.25
    # Liquidité générale (AC / PC) : ≥2.0 → 10 / ≤0.5 → 0
    BORNE_LIQ_MIN, BORNE_LIQ_MAX = 0.5, 2.0

    # -- Paliers notation ancienneté ------------------------------------
    PALIERS_ANCIENNETE = [(10, 10.0), (5, 7.0), (2, 5.0)]
    ANCIENNETE_DEFAUT = 2.0

    @staticmethod
    def _normaliser(valeur, borne_min, borne_max):
        """Normalisation linéaire entre borne_min (→0) et borne_max (→10)."""
        if valeur is None:
            return None
        if valeur >= borne_max:
            return 10.0
        if valeur <= borne_min:
            return 0.0
        return round(((valeur - borne_min) / (borne_max - borne_min)) * 10, 2)

    @classmethod
    def normaliser_solvabilite(cls, ratio):
        return cls._normaliser(ratio, cls.BORNE_SOLV_MIN, cls.BORNE_SOLV_MAX)

    @classmethod
    def normaliser_ebitda(cls, ratio):
        return cls._normaliser(ratio, cls.BORNE_EBITDA_MIN, cls.BORNE_EBITDA_MAX)

    @classmethod
    def normaliser_liquidite(cls, ratio):
        return cls._normaliser(ratio, cls.BORNE_LIQ_MIN, cls.BORNE_LIQ_MAX)

    @classmethod
    def noter_anciennete(cls, date_creation):
        """Note 0-10 calculée depuis la date de création de l'entreprise."""
        if not date_creation:
            return cls.ANCIENNETE_DEFAUT
        age_annees = (date.today() - date_creation).days / 365.25
        for seuil, note in cls.PALIERS_ANCIENNETE:
            if age_annees > seuil:
                return note
        return cls.ANCIENNETE_DEFAUT

    @classmethod
    def extraire_bilan(cls, acheteur, annee_int):
        """Extrait et normalise les 3 ratios financiers depuis le bilan classique."""
        result = {
            'solvabilite_ratio': None, 'solvabilite_note': None,
            'ebitda_ratio':      None, 'ebitda_note':      None,
            'liquidite_ratio':   None, 'liquidite_note':   None,
            'bilan_disponible':  False,
            'ca':                None,
            'fonds_propres':     None,
            'total_bilan':       None,
            'actif_circulant':   None,
            'passif_circulant':  None,
            'ebe':               None,
        }
        try:
            actif  = ActifC.objects.filter(acheteur=acheteur, annee__annee=annee_int).first()
            passif = PassifC.objects.filter(acheteur=acheteur, annee__annee=annee_int).first()
            restat = ResultatC.objects.filter(acheteur=acheteur, annee__annee=annee_int).first()

            if not (actif and passif):
                return result

            result['bilan_disponible'] = True

            total_bilan   = float(actif.general_total or 0)
            fonds_propres = float(passif.total_I or 0)
            actif_circ    = float(actif.total_II or 0)
            passif_circ   = float(passif.total_III or 0)

            result['total_bilan']     = round(total_bilan, 2)
            result['fonds_propres']   = round(fonds_propres, 2)
            result['actif_circulant'] = round(actif_circ, 2)
            result['passif_circulant']= round(passif_circ, 2)

            if total_bilan > 0:
                r = fonds_propres / total_bilan
                result['solvabilite_ratio'] = round(r, 4)
                result['solvabilite_note']  = cls.normaliser_solvabilite(r)

            if passif_circ > 0:
                r = actif_circ / passif_circ
                result['liquidite_ratio'] = round(r, 4)
                result['liquidite_note']  = cls.normaliser_liquidite(r)

            if restat:
                ca  = float(restat.ca or 0)
                ebe = float(restat.excedent_brut_ex or 0)
                result['ca']  = round(ca, 2)
                result['ebe'] = round(ebe, 2)
                if ca > 0:
                    r = ebe / ca
                    result['ebitda_ratio'] = round(r, 4)
                    result['ebitda_note']  = cls.normaliser_ebitda(r)
        except Exception as exc:
            logger.error(f"Erreur extraction bilan rating: {exc}")

        return result

    @classmethod
    def calculer(cls, solvabilite_note, ebitda_note, liquidite_note,
                 historique_paiement_note, anciennete_note,
                 secteur_activite_note, management_note):
        """Retourne le résultat complet du calcul."""
        def _f(v):
            try:
                return float(v or 0)
            except (TypeError, ValueError):
                return 0.0

        hp = _f(historique_paiement_note)

        if hp == 0:
            return {
                'score_final': 0.0,
                'red_flag': True,
                'rating': 'D',
                'classe_risque': 'Risque Critique',
                'decision': 'Refus automatique (Red Flag : historique de paiement nul)',
                'notes_brutes': {},
                'notes_ponderees': {},
            }

        notes = {
            'solvabilite':         _f(solvabilite_note),
            'ebitda':              _f(ebitda_note),
            'liquidite':           _f(liquidite_note),
            'historique_paiement': hp,
            'anciennete':          _f(anciennete_note),
            'secteur_activite':    _f(secteur_activite_note),
            'management':          _f(management_note),
        }

        notes_ponderees = {k: round(notes[k] * cls.COEFFICIENTS[k], 4) for k in notes}
        score_final = round(sum(notes_ponderees.values()), 2)
        rating, classe_risque, decision = cls.determiner_rating(score_final)

        return {
            'score_final': score_final,
            'red_flag': False,
            'rating': rating,
            'classe_risque': classe_risque,
            'decision': decision,
            'notes_brutes': notes,
            'notes_ponderees': notes_ponderees,
        }

    @staticmethod
    def determiner_rating(score):
        if score >= 8.5:
            return 'AAA/AA', 'Risque Excellent', 'Approbation immédiate (Conditions premium)'
        elif score >= 7.0:
            return 'A/BBB', 'Risque Faible / Bon', 'Approbation (Conditions standards)'
        elif score >= 5.5:
            return 'BB/B', 'Risque Modéré', 'Analyse humaine requise (Comité de crédit)'
        elif score >= 4.0:
            return 'CCC', 'Risque Élevé', 'Garanties obligatoires (Caution, nantissement)'
        else:
            return 'D', 'Risque Critique', 'Refus automatique'


# ======================================================================
#  Serializer inline (léger, pour les réponses API)
# ======================================================================
class ScoringRatingSerializer(serializers.ModelSerializer):
    annee_val       = serializers.IntegerField(source='annee.annee', read_only=True)
    acheteur_nom    = serializers.CharField(source='acheteur.nom', read_only=True)
    created_by_info = UserSimpleSerializer(source='created_by', read_only=True)
    updated_by_info = UserSimpleSerializer(source='updated_by', read_only=True)

    class Meta:
        model = ScoringRating
        fields = [
            'id', 'acheteur', 'acheteur_nom', 'annee', 'annee_val',
            'solvabilite_ratio', 'solvabilite_note',
            'ebitda_ratio', 'ebitda_note',
            'liquidite_ratio', 'liquidite_note',
            'historique_paiement_note', 'anciennete_note',
            'secteur_activite_note', 'management_note',
            'score_final', 'rating', 'classe_risque', 'decision', 'red_flag',
            'commentaire',
            'created_at', 'updated_at',
            'created_by', 'created_by_info',
            'updated_by', 'updated_by_info',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


# ======================================================================
#  Vues API
# ======================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_annees_rating(request, acheteur_id):
    """Années disponibles dans le bilan classique pour un acheteur."""
    acheteur = get_object_or_404(Acheteur, id=acheteur_id)
    annees = (
        ActifC.objects
        .filter(acheteur=acheteur)
        .exclude(annee__isnull=True)
        .values_list('annee__annee', flat=True)
        .distinct()
    )
    annees_list = sorted([a for a in annees if a is not None], reverse=True)
    annees_avec_rating = list(
        ScoringRating.objects
        .filter(acheteur=acheteur)
        .exclude(annee__isnull=True)
        .values_list('annee__annee', flat=True)
    )
    return Response({'years': annees_list, 'annees_avec_rating': annees_avec_rating})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def precharger_bilan_rating(request, acheteur_id, annee):
    """Extrait les ratios du bilan pour une année et retourne les notes pré-calculées."""
    acheteur = get_object_or_404(Acheteur, id=acheteur_id)
    bilan = ScoringRatingService.extraire_bilan(acheteur, annee)
    anciennete_note = ScoringRatingService.noter_anciennete(acheteur.date_creation)

    existing = None
    try:
        annee_obj = Annee.objects.get(annee=annee)
        obj = ScoringRating.objects.get(acheteur=acheteur, annee=annee_obj)
        existing = ScoringRatingSerializer(obj).data
    except (Annee.DoesNotExist, ScoringRating.DoesNotExist):
        pass

    return Response({'bilan': bilan, 'anciennete_note': anciennete_note, 'existing': existing})


class ScoringRatingCalculerView(APIView):
    """POST → calcule le score sans enregistrer (aperçu temps réel)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        d = request.data
        anciennete_note = ScoringRatingService.noter_anciennete(acheteur.date_creation)
        result = ScoringRatingService.calculer(
            solvabilite_note=d.get('solvabilite_note'),
            ebitda_note=d.get('ebitda_note'),
            liquidite_note=d.get('liquidite_note'),
            historique_paiement_note=d.get('historique_paiement_note'),
            anciennete_note=anciennete_note,
            secteur_activite_note=d.get('secteur_activite_note'),
            management_note=d.get('management_note'),
        )
        result['anciennete_note'] = anciennete_note
        return Response(result)


class ScoringRatingSauvegarderView(APIView):
    """GET list + POST create-or-update pour (acheteur, annee)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        qs = ScoringRating.objects.filter(acheteur=acheteur).select_related('annee').order_by('-annee__annee')
        return Response(ScoringRatingSerializer(qs, many=True).data)

    def post(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        d = request.data
        annee_int = d.get('annee_int')

        if not annee_int:
            return Response({'success': False, 'error': "L'année est requise."}, status=400)

        try:
            annee_obj = Annee.objects.get(annee=int(annee_int))
        except Annee.DoesNotExist:
            return Response({'success': False, 'error': f"L'année {annee_int} n'existe pas."}, status=400)

        bilan = ScoringRatingService.extraire_bilan(acheteur, int(annee_int))
        anciennete_note = ScoringRatingService.noter_anciennete(acheteur.date_creation)

        calc = ScoringRatingService.calculer(
            solvabilite_note=bilan.get('solvabilite_note'),
            ebitda_note=bilan.get('ebitda_note'),
            liquidite_note=bilan.get('liquidite_note'),
            historique_paiement_note=d.get('historique_paiement_note', 5),
            anciennete_note=anciennete_note,
            secteur_activite_note=d.get('secteur_activite_note', 5),
            management_note=d.get('management_note', 5),
        )

        defaults = {
            'solvabilite_ratio':       bilan.get('solvabilite_ratio'),
            'solvabilite_note':        bilan.get('solvabilite_note'),
            'ebitda_ratio':            bilan.get('ebitda_ratio'),
            'ebitda_note':             bilan.get('ebitda_note'),
            'liquidite_ratio':         bilan.get('liquidite_ratio'),
            'liquidite_note':          bilan.get('liquidite_note'),
            'anciennete_note':         anciennete_note,
            'historique_paiement_note': d.get('historique_paiement_note', 5),
            'secteur_activite_note':   d.get('secteur_activite_note', 5),
            'management_note':         d.get('management_note', 5),
            'score_final':             calc['score_final'],
            'rating':                  calc['rating'],
            'classe_risque':           calc['classe_risque'],
            'decision':                calc['decision'],
            'red_flag':                calc['red_flag'],
            'commentaire':             d.get('commentaire', ''),
            'updated_by':              request.user,
        }

        try:
            obj, created = ScoringRating.objects.update_or_create(
                acheteur=acheteur, annee=annee_obj, defaults=defaults
            )
            if created:
                obj.created_by = request.user
                obj.save(update_fields=['created_by'])

            return Response({
                'success': True,
                'created': created,
                'data': ScoringRatingSerializer(obj).data,
                'calcul': calc,
            })
        except Exception as exc:
            logger.error(f"Erreur sauvegarde ScoringRating: {exc}")
            return Response({'success': False, 'error': str(exc)}, status=500)
