from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from main.serializers import *

import traceback
import logging
logger = logging.getLogger(__name__)

# === Vues Acheteur === #

class AcheteursParMois(APIView):
    def get(self, request):
        acheteurs_par_mois = Acheteur.objects.annotate(
            mois=TruncMonth('created_at')
        ).values('mois').annotate(
            total=Count('id')
        ).order_by('mois')

        # Dictionnaire pour mapper les noms des mois en français
        mois_en_francais = {
            'January': 'Janvier',
            'February': 'Février',
            'March': 'Mars',
            'April': 'Avril',
            'May': 'Mai',
            'June': 'Juin',
            'July': 'Juillet',
            'August': 'Août',
            'September': 'Septembre',
            'October': 'Octobre',
            'November': 'Novembre',
            'December': 'Décembre'
        }

        data = {
            'labels': [mois_en_francais[entry['mois'].strftime('%B')]  for entry in acheteurs_par_mois],
            'data': [entry['total'] for entry in acheteurs_par_mois]
        }
        return Response(data)


class ListAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Récupérer le pays sélectionné
        selected_pays_id = request.session.get('selected_pays_id', request.user.pays.id)
        
        # Initialiser le queryset
        acheteur_list = Acheteur.objects.filter(pays_id=selected_pays_id)
        
        # Récupérer les paramètres de requête
        search_query = request.query_params.get("search", "")
        page_number = int(request.query_params.get("page", 1))
        items_per_page = int(request.query_params.get("page_size", 10))
        sort_field = request.query_params.get("sort", "nom")
        sort_dir = request.query_params.get("sort_dir", "asc")
        filter_type = request.query_params.get("filter", "all")
        
        # Appliquer le filtre
        now = timezone.now()
        if filter_type == "active":
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            acheteur_list = acheteur_list.filter(updated_at__gte=start_of_month)
        elif filter_type == "new":
            start_of_week = now - timezone.timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            acheteur_list = acheteur_list.filter(created_at__gte=start_of_week)
        
        # Appliquer la recherche
        if search_query:
            acheteur_list = acheteur_list.filter(
                Q(code__icontains=search_query)
                | Q(nom__icontains=search_query)
                | Q(sigle__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(numero_adresse__icontains=search_query)
                | Q(site_internet__icontains=search_query)
                | Q(rue_adresse__icontains=search_query)
                | Q(activite_principale__icontains=search_query)
                | Q(categorie_entreprise__libelle__icontains=search_query)
                | Q(forme_juridique__libelle__icontains=search_query)
                | Q(statut_entreprise__libelle__icontains=search_query)
                | Q(pays__nom__icontains=search_query)
                | Q(province__nom__icontains=search_query)
                | Q(ville__nom__icontains=search_query)
            )
        
        # Appliquer le tri
        if sort_field:
            if sort_dir == "desc":
                sort_field = f"-{sort_field}"
            acheteur_list = acheteur_list.order_by(sort_field)
        else:
            acheteur_list = acheteur_list.order_by("nom")
        
        # Pagination
        paginator = Paginator(acheteur_list, items_per_page)
        
        try:
            acheteur_page = paginator.page(page_number)
        except PageNotAnInteger:
            acheteur_page = paginator.page(1)
        except EmptyPage:
            acheteur_page = paginator.page(paginator.num_pages)
        
        # Sérialisation
        serializer = AcheteurSerializer(acheteur_page, many=True)
        
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": acheteur_page.has_next(),
            "previous": acheteur_page.has_previous(),
            "current_page": page_number
        })

class SearchAcheteurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "").strip()
        page_number = request.query_params.get("page", 1)
        
        if not search_term:
            return Response({
                "success": False,
                "detail": "Terme de recherche manquant."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1
        
        # Récupérer le pays sélectionné
        selected_pays_id = request.session.get('selected_pays_id', request.user.pays.id if request.user.pays else None)
        
        # Construction de la requête optimisée
        acheteur_query = Acheteur.objects.select_related(
            'pays', 'ville', 'province', 
            'categorie_entreprise', 'forme_juridique', 'statut_entreprise'
        )
        
        # Filtrer par pays si spécifié
        if selected_pays_id:
            acheteur_query = acheteur_query.filter(pays_id=selected_pays_id)
        
        # Recherche avancée
        acheteur_query = acheteur_query.filter(
            Q(code__icontains=search_term) |
            Q(nom__icontains=search_term) |
            Q(sigle__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(activite_principale__icontains=search_term) |
            Q(pays__nom__icontains=search_term) |
            Q(ville__nom__icontains=search_term) |
            Q(province__nom__icontains=search_term) |
            Q(categorie_entreprise__libelle__icontains=search_term) |
            Q(forme_juridique__libelle__icontains=search_term) |
            Q(statut_entreprise__libelle__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(commentaire__icontains=search_term) |
            Q(site_internet__icontains=search_term)
        ).order_by("nom")
        
        # Pagination
        paginator = Paginator(acheteur_query, 10)
        
        try:
            acheteur_page = paginator.page(page_number)
        except PageNotAnInteger:
            acheteur_page = paginator.page(1)
            page_number = 1
        except EmptyPage:
            acheteur_page = paginator.page(paginator.num_pages)
            page_number = paginator.num_pages
        
        # Sérialiser les données
        serializer = AcheteurSerializer(acheteur_page, many=True)
        
        # Calculer les indices
        total_items = paginator.count
        items_per_page = paginator.per_page
        start_index = (page_number - 1) * items_per_page + 1
        end_index = min(page_number * items_per_page, total_items)
        
        return Response({
            "success": True,
            "results": serializer.data,
            "pagination": {
                "total": total_items,
                "per_page": items_per_page,
                "current_page": page_number,
                "total_pages": paginator.num_pages,
                "start_index": start_index,
                "end_index": end_index,
                "has_next": acheteur_page.has_next(),
                "has_previous": acheteur_page.has_previous(),
                "next_page": acheteur_page.next_page_number() if acheteur_page.has_next() else None,
                "previous_page": acheteur_page.previous_page_number() if acheteur_page.has_previous() else None,
            },
            "search_term": search_term,
            "message": f"{total_items} acheteur(s) trouvé(s) pour '{search_term}'"
        })


class AddAcheteurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            # Préparer les données
            data = request.data.copy()
            
            # Nettoyer les URLs
            # Nettoyer et formater le site_internet
            if 'site_internet' in data and data['site_internet']:
                site = data['site_internet'].strip()
                # Supprimer les préfixes http/https s'ils sont présents
                site = site.replace('https://', '').replace('http://', '')
                # Ajouter https:// pour la validation Django
                data['site_internet'] = f'https://{site}' if site else ''
            
            # Validation des données requises
            required_fields = ['nom', 'date_creation', 'activite_principale', 
                              'statut_entreprise', 'forme_juridique', 'pays',
                              'province', 'ville', 'couleur_commentaire', 'commentaire']
            
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return Response({
                    "success": False,
                    "message": "Champs obligatoires manquants",
                    "missing_fields": missing_fields,
                    "errors": {field: ["Ce champ est obligatoire"] for field in missing_fields}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Valider les relations
            try:
                pays = Pays.objects.get(id=data['pays'])
                province = Province.objects.get(id=data['province'])
                ville = Ville.objects.get(id=data['ville'])
                
                # Vérifier la cohérence géographique
                if province.pays_id != pays.id:
                    return Response({
                        "success": False,
                        "message": "Incohérence géographique",
                        "errors": {
                            "province": ["Cette province n'appartient pas au pays sélectionné"]
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if ville.province_id != province.id:
                    return Response({
                        "success": False,
                        "message": "Incohérence géographique",
                        "errors": {
                            "ville": ["Cette ville n'appartient pas à la province sélectionnée"]
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except (Pays.DoesNotExist, Province.DoesNotExist, Ville.DoesNotExist):
                return Response({
                    "success": False,
                    "message": "Données géographiques invalides",
                    "errors": {
                        "pays": ["Pays invalide"],
                        "province": ["Province invalide"],
                        "ville": ["Ville invalide"]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validation avec le serializer
            serializer = AddAcheteurSerializer(data=data, context={'request': request})
            
            if serializer.is_valid():
                try:
                    with transaction.atomic():
                        acheteur = serializer.save()
                        
                        # Créer un log d'activité
                        ActivityLog.objects.create(
                            user=request.user,
                            action_type='ACHETEUR_CREATED',
                            object_id=acheteur.id,
                            object_type='Acheteur',
                            details=f"Acheteur '{acheteur.nom}' créé par {request.user.username}",
                            ip_address=request.META.get('REMOTE_ADDR', '')
                        )
                        
                        # Envoyer une notification si configuré
                        if hasattr(settings, 'NOTIFY_ON_ACHETEUR_CREATE') and settings.NOTIFY_ON_ACHETEUR_CREATE:
                            self.send_notification(request.user, acheteur)
                        
                        return Response({
                            "success": True,
                            "message": "Acheteur créé avec succès",
                            "acheteur": serializer.data,
                            "redirect_url": f"/acheteurs/{acheteur.id}/detail/"
                        }, status=status.HTTP_201_CREATED)
                        
                except Exception as e:
                    return Response({
                        "success": False,
                        "message": "Erreur lors de la création",
                        "error": str(e),
                        "errors": serializer.errors
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                "success": False,
                "message": "Erreurs de validation",
                "errors": serializer.errors,
                "debug": {
                    "data_received": data,
                    "user": request.user.username,
                    "pays_id": data.get('pays')
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": "Erreur interne du serveur",
                "error": str(e),
                "traceback": traceback.format_exc() if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def send_notification(self, user, acheteur):
        """Envoie une notification pour la création d'un acheteur"""
        try:
            # Configuration des notifications
            notification_data = {
                'title': f'Nouvel acheteur ajouté',
                'message': f'{user.get_full_name() or user.username} a ajouté un nouvel acheteur: {acheteur.nom}',
                'type': 'acheteur_created',
                'acheteur_id': acheteur.id,
                'acheteur_nom': acheteur.nom,
                'created_by': user.username,
                'timestamp': timezone.now().isoformat()
            }
            
            # Log pour débogage
            logger.info(f"Notification acheteur créé: {notification_data}")
            
        except Exception as e:
            logger.error(f"Erreur envoi notification: {str(e)}")



class EditAcheteurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, id):
        """Récupère l'acheteur ou retourne 404"""
        try:
            return Acheteur.objects.select_related(
                'pays', 'ville', 'province', 
                'categorie_entreprise', 'forme_juridique', 'statut_entreprise'
            ).get(id=id)
        except Acheteur.DoesNotExist:
            return None
    
    def get(self, request, id, *args, **kwargs):
        acheteur = self.get_object(id)
        if not acheteur:
            return Response({
                "success": False,
                "detail": "Acheteur non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = GetAcheteurSerializer(acheteur)
        return Response({
            "success": True,
            "acheteur": serializer.data
        })
    
    def put(self, request, id, *args, **kwargs):
        print("=== DEBUG PUT REQUEST ===")
        print("Données reçues:", request.data)
        print("Headers:", request.headers)
        
        acheteur = self.get_object(id)
        if not acheteur:
            return Response({
                "success": False,
                "detail": "Acheteur non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = EditAcheteurSerializer(acheteur, data=request.data, partial=True)
        
        print("Serializer valide?", serializer.is_valid())
        
        if serializer.is_valid():
            try:
                instance = serializer.save()
                print("Instance sauvegardée avec succès")
                
                # Serializer pour la réponse
                response_serializer = GetAcheteurSerializer(instance)
                return Response({
                    "success": True,
                    "message": "Acheteur mis à jour avec succès.",
                    "acheteur": response_serializer.data
                })
            except Exception as e:
                print("Erreur lors de la sauvegarde:", str(e))
                return Response({
                    "success": False,
                    "error": f"Erreur lors de la mise à jour: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        print("Erreurs du serializer:", serializer.errors)
        return Response({
            "success": False,
            "errors": serializer.errors,
            "message": "Erreurs de validation."
        }, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        
        if not ids or not isinstance(ids, list):
            return Response({
                "success": False,
                "error": "Une liste d'IDs est requise."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que l'utilisateur a la permission
        if not request.user.role in ['Root', 'Admin']:
            return Response({
                "success": False,
                "error": "Vous n'avez pas la permission de supprimer des acheteurs."
            }, status=status.HTTP_403_FORBIDDEN)
        
        acheteurs = Acheteur.objects.filter(id__in=ids)
        
        if not acheteurs.exists():
            return Response({
                "success": False,
                "error": "Aucun acheteur trouvé pour les IDs fournis."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            count = acheteurs.count()
            acheteurs.delete()
            
            return Response({
                "success": True,
                "message": f"{count} acheteur(s) supprimé(s) avec succès."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Erreur lors de la suppression: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAcheteurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id, *args, **kwargs):
        try:
            acheteur = Acheteur.objects.select_related(
                'pays', 'ville', 'province', 
                'categorie_entreprise', 'forme_juridique', 'statut_entreprise'
            ).get(id=id)
            
            serializer = GetAcheteurSerializer(acheteur)
            return Response({
                "success": True,
                "acheteur": serializer.data
            })
            
        except Acheteur.DoesNotExist:
            return Response({
                "success": False,
                "detail": "Acheteur non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)



class AcheteurStatsView(APIView):
    """Vue pour obtenir les statistiques des acheteurs"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            print("=== DEBUG AcheteurStatsView ===")
            
            # 1. Récupérer le pays sélectionné
            selected_pays_id = None
            
            # Priorité 1: Pays de l'utilisateur
            if hasattr(request.user, 'pays') and request.user.pays:
                selected_pays_id = request.user.pays.id
                print(f"Pays depuis utilisateur: {selected_pays_id}")
            
            # Priorité 2: Pays de la session
            if not selected_pays_id:
                selected_pays_id = request.session.get('selected_pays_id')
                print(f"Pays depuis session: {selected_pays_id}")
            
            # Priorité 3: Premier pays disponible
            if not selected_pays_id:
                from main.models import Pays
                first_pays = Pays.objects.first()
                if first_pays:
                    selected_pays_id = first_pays.id
                    print(f"Pays par défaut: {selected_pays_id}")
            
            print(f"Pays sélectionné final: {selected_pays_id}")
            
            # 2. Filtrer les acheteurs
            acheteurs = Acheteur.objects.all()
            if selected_pays_id:
                acheteurs = acheteurs.filter(pays_id=selected_pays_id)
            
            total_count = acheteurs.count()
            print(f"Total acheteurs: {total_count}")
            
            # 3. Calculer les dates
            from django.utils import timezone
            now = timezone.now()
            print(f"Heure actuelle: {now}")
            
            # Ce mois
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month = acheteurs.filter(created_at__gte=start_of_month).count()
            print(f"Start of month: {start_of_month}")
            print(f"Acheteurs ce mois: {this_month}")
            
            # Cette semaine (lundi à 00:00:00)
            import datetime
            start_of_week = now - datetime.timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            this_week = acheteurs.filter(created_at__gte=start_of_week).count()
            print(f"Start of week: {start_of_week}")
            print(f"Acheteurs cette semaine: {this_week}")
            
            # 4. Nom du pays actif
            active_country = "Tous pays"
            if selected_pays_id:
                from main.models import Pays
                pays = Pays.objects.filter(id=selected_pays_id).first()
                if pays:
                    active_country = pays.nom
            print(f"Pays actif: {active_country}")
            
            # 5. Retourner la structure ATTENDUE par le JavaScript
            stats = {
                'total': total_count,
                'thisMonth': this_month,
                'thisWeek': this_week,
                'activeCountry': active_country
            }
            
            print(f"Stats à retourner: {stats}")
            
            return Response(stats)
            
        except Exception as e:
            import traceback
            print(f"ERREUR dans AcheteurStatsView: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return Response({
                'total': 0,
                'thisMonth': 0,
                'thisWeek': 0,
                'activeCountry': 'Erreur'
            }, status=200)  # Toujours retourner 200 pour éviter les erreurs AJAX
        from django.db.models import Count, Q
        
        # Récupérer le pays sélectionné
        selected_pays_id = request.session.get('selected_pays_id', request.user.pays.id if request.user.pays else None)
        
        # Base queryset
        queryset = Acheteur.objects.all()
        if selected_pays_id:
            queryset = queryset.filter(pays_id=selected_pays_id)
        
        stats = {
            'total': queryset.count(),
            'actifs': queryset.filter(
                Q(statut_entreprise__libelle__icontains='actif') | 
                Q(statut_entreprise__isnull=True)
            ).count(),
            'inactifs': queryset.filter(
                Q(statut_entreprise__libelle__icontains='inactif')
            ).count(),
            'par_pays': list(queryset.values('pays__nom').annotate(
                total=Count('id')
            ).order_by('-total')),
            'derniers_ajouts': list(queryset.order_by('-created_at')[:5].values(
                'id', 'nom', 'created_at'
            ))
        }
        
        return Response({
            "success": True,
            "stats": stats,
            "selected_pays_id": selected_pays_id
        })