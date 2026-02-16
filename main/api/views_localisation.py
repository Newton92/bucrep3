from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.serializers import *

import logging
logger = logging.getLogger(__name__)

# === Vues Localisation === #


import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import models
from main.models import Pays  # Assurez-vous que ce chemin est correct

logger = logging.getLogger(__name__)

class PaysCarteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            logger.info(f"User {request.user} appelle /api/pays-carte/")
            
            # Mapping des codes vers ISO A2 - COMPLÉTÉ
            code_mapping = {
                # Pays déjà présents
                "BEN": "BJ",    # Bénin
                "CMR": "CM",    # Cameroun
                "CIV": "CI",    # Côte d'Ivoire
                "GAB": "GA",    # Gabon
                "GHA": "GH",    # Ghana
                "MLI": "ML",    # Mali (GeoJSON utilise "MLI")
                "MAR": "MA",    # Maroc (GeoJSON utilise "MAR")
                "SEN": "SN",    # Sénégal
                
                # Nouveaux pays africains extraits du GeoJSON
                "AGO": "AO",    # Angola
                "BDI": "BI",    # Burundi
                "BFA": "BF",    # Burkina Faso
                "CAF": "CF",    # République centrafricaine
                "COD": "CD",    # République démocratique du Congo
                "COG": "CG",    # République du Congo
                "DJI": "DJ",    # Djibouti
                "DZA": "DZ",    # Algérie
                "EGY": "EG",    # Égypte
                "ERI": "ER",    # Érythrée
                "ETH": "ET",    # Éthiopie
                "GIN": "GN",    # Guinée
                "GMB": "GM",    # Gambie
                "GNB": "GW",    # Guinée-Bissau
                "GNQ": "GQ",    # Guinée équatoriale
                "KEN": "KE",    # Kenya
                "LBR": "LR",    # Liberia
                "LBY": "LY",    # Libye
                "LSO": "LS",    # Lesotho
                "MDG": "MG",    # Madagascar
                "MOZ": "MZ",    # Mozambique
                "MRT": "MR",    # Mauritanie
                "MWI": "MW",    # Malawi
                "NAM": "NA",    # Namibie
                "NER": "NE",    # Niger
                "NGA": "NG",    # Nigeria
                "RWA": "RW",    # Rwanda
                "SDN": "SD",    # Soudan
                "SLE": "SL",    # Sierra Leone
                "SOM": "SO",    # Somalie
                "SSD": "SS",    # Soudan du Sud
                "SWZ": "SZ",    # Eswatini (Swaziland)
                "TCD": "TD",    # Tchad
                "TGO": "TG",    # Togo
                "TZA": "TZ",    # Tanzanie
                "UGA": "UG",    # Ouganda
                "ZAF": "ZA",    # Afrique du Sud
                "ZMB": "ZM",    # Zambie
                "ZWE": "ZW",    # Zimbabwe
                "TUN": "TN",    # Tunisie
            }

            # Coordonnées des capitales africaines - COMPLÉTÉ
            capitales_coords = {
                # Capitales déjà présentes
                "BJ": {"lat": 6.3725, "lng": 2.3914, "capitale": "Porto-Novo"},
                "CM": {"lat": 3.8480, "lng": 11.5021, "capitale": "Yaoundé"},
                "CI": {"lat": 5.3594, "lng": -4.0083, "capitale": "Abidjan"},
                "GA": {"lat": 0.4162, "lng": 9.4673, "capitale": "Libreville"},
                "GH": {"lat": 5.6037, "lng": -0.1870, "capitale": "Accra"},
                "ML": {"lat": 12.6392, "lng": -8.0029, "capitale": "Bamako"},
                "MA": {"lat": 33.9716, "lng": -6.8498, "capitale": "Rabat"},
                "SN": {"lat": 14.6928, "lng": -17.4467, "capitale": "Dakar"},
                
                # Nouvelles capitales africaines
                "AO": {"lat": -8.8383, "lng": 13.2344, "capitale": "Luanda"},
                "BI": {"lat": -3.3614, "lng": 29.3599, "capitale": "Gitega"},
                "BF": {"lat": 12.3714, "lng": -1.5197, "capitale": "Ouagadougou"},
                "CF": {"lat": 4.3947, "lng": 18.5582, "capitale": "Bangui"},
                "CD": {"lat": -4.3250, "lng": 15.3222, "capitale": "Kinshasa"},
                "CG": {"lat": -4.2634, "lng": 15.2429, "capitale": "Brazzaville"},
                "DJ": {"lat": 11.5721, "lng": 43.1456, "capitale": "Djibouti"},
                "DZ": {"lat": 36.7538, "lng": 3.0588, "capitale": "Alger"},
                "EG": {"lat": 30.0444, "lng": 31.2357, "capitale": "Le Caire"},
                "ER": {"lat": 15.3229, "lng": 38.9251, "capitale": "Asmara"},
                "ET": {"lat": 9.0320, "lng": 38.7469, "capitale": "Addis-Abeba"},
                "GN": {"lat": 9.6412, "lng": -13.5784, "capitale": "Conakry"},
                "GM": {"lat": 13.4549, "lng": -16.5790, "capitale": "Banjul"},
                "GW": {"lat": 11.8636, "lng": -15.5846, "capitale": "Bissau"},
                "GQ": {"lat": 3.7523, "lng": 8.7741, "capitale": "Malabo"},
                "KE": {"lat": -1.2921, "lng": 36.8219, "capitale": "Nairobi"},
                "LR": {"lat": 6.3008, "lng": -10.7972, "capitale": "Monrovia"},
                "LY": {"lat": 32.8872, "lng": 13.1913, "capitale": "Tripoli"},
                "LS": {"lat": -29.3101, "lng": 27.4786, "capitale": "Maseru"},
                "MG": {"lat": -18.8792, "lng": 47.5079, "capitale": "Antananarivo"},
                "MZ": {"lat": -25.9692, "lng": 32.5732, "capitale": "Maputo"},
                "MR": {"lat": 18.0731, "lng": -15.9582, "capitale": "Nouakchott"},
                "MW": {"lat": -13.9626, "lng": 33.7741, "capitale": "Lilongwe"},
                "NA": {"lat": -22.5609, "lng": 17.0658, "capitale": "Windhoek"},
                "NE": {"lat": 13.5127, "lng": 2.1126, "capitale": "Niamey"},
                "NG": {"lat": 9.0765, "lng": 7.3986, "capitale": "Abuja"},
                "RW": {"lat": -1.9500, "lng": 30.0588, "capitale": "Kigali"},
                "SD": {"lat": 15.5007, "lng": 32.5599, "capitale": "Khartoum"},
                "SL": {"lat": 8.4840, "lng": -13.2299, "capitale": "Freetown"},
                "SO": {"lat": 2.0469, "lng": 45.3182, "capitale": "Mogadiscio"},
                "SS": {"lat": 4.8594, "lng": 31.5713, "capitale": "Djouba"},
                "SZ": {"lat": -26.3054, "lng": 31.1367, "capitale": "Mbabane"},
                "TD": {"lat": 12.1348, "lng": 15.0557, "capitale": "N'Djamena"},
                "TG": {"lat": 6.1375, "lng": 1.2123, "capitale": "Lomé"},
                "TZ": {"lat": -6.1630, "lng": 35.7516, "capitale": "Dodoma"},
                "UG": {"lat": 0.3136, "lng": 32.5811, "capitale": "Kampala"},
                "ZA": {"lat": -25.7313, "lng": 28.2184, "capitale": "Pretoria"},
                "ZM": {"lat": -15.3875, "lng": 28.3228, "capitale": "Lusaka"},
                "ZW": {"lat": -17.8252, "lng": 31.0335, "capitale": "Harare"},
                "TN": {"lat": 36.8065, "lng": 10.1815, "capitale": "Tunis"},
            }
            
            
            # Récupérer tous les pays
            pays = Pays.objects.all()
            
            if not pays.exists():
                logger.warning("Aucun pays trouvé dans la base de données")
                return Response({
                    "message": "Aucun pays configuré",
                    "data": []
                }, status=status.HTTP_200_OK)
            
            pays_data = []
            for p in pays:
                # Utiliser le mapping pour convertir en ISO A2
                iso_code = code_mapping.get(p.code, p.code)
                capitale_info = capitales_coords.get(iso_code, {})
                
                pays_data.append({
                    "id": p.id,
                    "nom": p.nom,
                    "code": p.code,  # Code original
                    "iso_code": iso_code,  # Code ISO A2
                    "is_active": p.is_active if hasattr(p, 'is_active') else True,
                    "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') and p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if hasattr(p, 'updated_at') and p.updated_at else None,
                    "capitale": capitale_info.get("capitale", ""),
                    "latitude": capitale_info.get("lat"),
                    "longitude": capitale_info.get("lng")
                })
            
            logger.info(f"{len(pays_data)} pays retournés")
            return Response(pays_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur dans PaysCarteView: {str(e)}", exc_info=True)
            return Response({
                "error": "Erreur serveur",
                "detail": str(e),
                "timestamp": timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaysStatistiquesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retourne les statistiques globales des pays"""
        total_pays = Pays.objects.count()
        pays_actifs = Pays.objects.filter(is_active=True).count()
        pays_inactifs = total_pays - pays_actifs
        
        # Derniers pays ajoutés
        derniers_pays = Pays.objects.order_by('-created_at')[:5].values('nom', 'code', 'created_at')
        
        return Response({
            "statistiques": {
                "total": total_pays,
                "actifs": pays_actifs,
                "inactifs": pays_inactifs,
                "taux_activation": round((pays_actifs / total_pays * 100) if total_pays > 0 else 0, 2)
            },
            "derniers_ajouts": list(derniers_pays),
            "timestamp": timezone.now().isoformat()
        })
        
        
class PaysDebugView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        import traceback
        try:
            from main.models import Pays
            pays = Pays.objects.all()
            return Response({
                "count": pays.count(),
                "pays": list(pays.values('id', 'nom', 'code', 'is_active')),
                "user": str(request.user)
            })
        except Exception as e:
            return Response({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, status=500)


class ListPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        pays_list = Pays.objects.filter(
            Q(nom__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by("nom")

        paginator = Paginator(pays_list, 10)  # 10 items par page
        pays_page = paginator.get_page(page_number)
        serializer = PaysSerializer(pays_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": pays_page.has_next(),
                "previous": pays_page.has_previous(),
            }
        )


class SearchPaysView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pays = Pays.objects.filter(nom__icontains=search_term).order_by("nom")
        paginator = Paginator(pays, 10)  # Nombre d'éléments par page
        page_number = request.query_params.get("page")
        page_obj = paginator.get_page(page_number)
        serializer = PaysSerializer(page_obj, many=True)
        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": page_obj.has_next(),
                "previous": page_obj.has_previous(),
            }
        )


class AddPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaysSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            pays = Pays.objects.get(id=id)
        except Pays.DoesNotExist:
            return Response(
                {"detail": "Pays non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = PaysSerializer(pays)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            pays = Pays.objects.get(id=id)
        except Pays.DoesNotExist:
            return Response(
                {"detail": "Pays non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = PaysSerializer(pays, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeletePaysView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids")
        if not ids:
            return Response(
                {"detail": "Aucun ID de pays fourni."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pays = Pays.objects.filter(id__in=ids)
        pays.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListProvincesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)
        pays_id = request.query_params.get(
            "pays"
        )  # Récupère l'ID du pays depuis la requête

        provinces_list = Province.objects.all()

        # Filtrer par pays si un ID est fourni
        if pays_id:
            provinces_list = provinces_list.filter(pays_id=pays_id)

        # Filtrer par recherche si nécessaire
        if search_query:
            provinces_list = provinces_list.filter(
                Q(nom__icontains=search_query) | Q(code__icontains=search_query)
            )

        provinces_list = provinces_list.order_by("nom")

        paginator = Paginator(provinces_list, 10)  # 10 items par page
        provinces_page = paginator.get_page(page_number)
        serializer = ProvinceSerializer(provinces_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": provinces_page.has_next(),
                "previous": provinces_page.has_previous(),
            }
        )


class ListProvincesByCountryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        country_id = self.kwargs.get("country_id")
        provinces = Province.objects.filter(pays_id=country_id).order_by("nom")
        serializer = ProvinceSerializer(provinces, many=True)
        return Response({"results": serializer.data})


class AddProvinceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddProvinceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditProvinceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            province = Province.objects.get(id=id)
        except Province.DoesNotExist:
            return Response(
                {"detail": "Province non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProvinceSerializer(province)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            province = Province.objects.get(id=id)
        except Province.DoesNotExist:
            return Response(
                {"detail": "Province non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateProvinceSerializer(province, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        print(serializer.errors)  # Ajoutez ce log
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteProvincesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids")
        if not ids:
            return Response(
                {"detail": "Aucun ID de province fourni."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provinces = Province.objects.filter(id__in=ids)
        provinces.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListVillesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        villes_list = Ville.objects.filter(
            Q(nom__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by("nom")

        paginator = Paginator(villes_list, 10)  # 10 items par page
        villes_page = paginator.get_page(page_number)
        serializer = VilleSerializer(villes_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": villes_page.has_next(),
                "previous": villes_page.has_previous(),
            }
        )


class ListVillesByProvinceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        province_id = self.kwargs.get("province_id")
        villes = Ville.objects.filter(province_id=province_id).order_by("nom")
        serializer = VilleProvinceSerializer(villes, many=True)
        return Response({"results": serializer.data})


class AddVilleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddVilleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditVilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            ville = Ville.objects.get(id=id)
        except Ville.DoesNotExist:
            return Response(
                {"detail": "Ville non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = VilleSerializer(ville)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            ville = Ville.objects.get(id=id)
        except Ville.DoesNotExist:
            return Response(
                {"detail": "Ville non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateVilleSerializer(ville, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteVillesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids")
        if not ids:
            return Response(
                {"detail": "Aucun ID de ville fourni."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        villes = Ville.objects.filter(id__in=ids)
        deleted_count = villes.count()
        villes.delete()
        return Response(
            {"detail": f"{deleted_count} ville(s) supprimée(s)."},
            status=status.HTTP_204_NO_CONTENT,
        )
