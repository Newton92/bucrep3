# views_scoring_delphi.py — API pour le Score Commercial Delphi ACREMAC

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Acheteur, ScoringDelphi
from main.serializers import ScoringDelphiSerializer


class ScoringDelphiAcheteurView(APIView):
    """GET + POST/PUT du score Delphi pour un acheteur donné (OneToOne)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id):
        get_object_or_404(Acheteur, id=acheteur_id)
        try:
            obj = ScoringDelphi.objects.select_related(
                'acheteur', 'created_by', 'updated_by'
            ).get(acheteur_id=acheteur_id)
            return Response({'exists': True, 'data': ScoringDelphiSerializer(obj, context={'request': request}).data})
        except ScoringDelphi.DoesNotExist:
            return Response({'exists': False, 'data': None})

    def post(self, request, acheteur_id):
        get_object_or_404(Acheteur, id=acheteur_id)
        try:
            obj = ScoringDelphi.objects.get(acheteur_id=acheteur_id)
            serializer = ScoringDelphiSerializer(
                obj, data=request.data, partial=True, context={'request': request}
            )
        except ScoringDelphi.DoesNotExist:
            data = request.data.copy()
            data['acheteur'] = acheteur_id
            serializer = ScoringDelphiSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            instance = serializer.save()
            return Response(
                {'success': True, 'data': ScoringDelphiSerializer(instance, context={'request': request}).data},
                status=status.HTTP_200_OK,
            )
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def autofill_delphi(request, acheteur_id):
    """
    Retourne les valeurs financières calculées depuis les bilans existants,
    sans modifier le ScoringDelphi. Utile pour pré-remplir le formulaire.
    """
    acheteur = get_object_or_404(Acheteur, id=acheteur_id)
    tmp = ScoringDelphi(acheteur=acheteur)
    suggestions = tmp.prefill_from_bilan(force=True)
    return Response({'suggestions': suggestions})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simuler_score_delphi(request, acheteur_id):
    """
    Calcule et retourne un score Delphi simulé sans l'enregistrer.
    Utile pour l'aperçu en temps réel dans le formulaire.
    """
    get_object_or_404(Acheteur, id=acheteur_id)
    # On construit un objet temporaire (pas sauvegardé) pour utiliser le service
    data = request.data

    def _float(key, default=None):
        try:
            v = data.get(key)
            return float(v) if v not in (None, '', 'null') else default
        except (ValueError, TypeError):
            return default

    def _int(key, default=0):
        try:
            v = data.get(key)
            return int(v) if v not in (None, '', 'null') else default
        except (ValueError, TypeError):
            return default

    def _bool(key):
        v = data.get(key)
        if isinstance(v, bool):
            return v
        return str(v).lower() in ('true', '1', 'yes')

    tmp = ScoringDelphi(
        acheteur_id=acheteur_id,
        dbt=_float('dbt', 0),
        tendance_dbt_hausse=_bool('tendance_dbt_hausse'),
        montants_contestes=_float('montants_contestes'),
        est_en_liquidation=_bool('est_en_liquidation'),
        petition_faillite=_bool('petition_faillite'),
        nb_procedures_collectives=_int('nb_procedures_collectives'),
        nb_inscriptions_privileges=_int('nb_inscriptions_privileges'),
        nb_jugements_tribunaux=_int('nb_jugements_tribunaux'),
        ratio_liquidite=_float('ratio_liquidite'),
        marge_nette=_float('marge_nette'),
        ebitda_ratio=_float('ebitda_ratio'),
        ratio_endettement=_float('ratio_endettement'),
        retard_depot_bilan=_bool('retard_depot_bilan'),
        age_entreprise=_float('age_entreprise'),
        historique_dirigeants_negatif=_bool('historique_dirigeants_negatif'),
    )
    score = tmp.calculer_score()
    bande, etoiles, niveau = ScoringDelphi.determiner_bande_et_risque(score)
    return Response({
        'score': score,
        'bande': bande,
        'etoiles': etoiles,
        'niveau_risque': niveau,
    })
