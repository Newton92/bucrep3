from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count
from datetime import timedelta

from main.serializers import *
from main.models import Acheteur, Pays, NaceSpecifique

import traceback
import logging
logger = logging.getLogger(__name__)


def _resolve_selected_pays_id(request, persist=True):
    """
    Résout le pays actif avec la priorité suivante :
      1. session['selected_pays_id']  — changement en cours via la toolbar
      2. user.pays_actif_id           — dernier pays persisté en DB (survit aux reconnexions)
      3. user.pays                    — affectation statique de l'employé
      4. None                         — aucun filtre (superadmin, etc.)
    """
    selected_pays_id = None

    # 1. Session (priorité maximale : changement toolbar en cours de session)
    session_value = request.session.get("selected_pays_id")
    if session_value:
        try:
            sid = int(session_value)
        except (TypeError, ValueError):
            sid = None
        if sid and Pays.objects.filter(id=sid, afficher_au_dashboard=True).exists():
            selected_pays_id = sid

    # 2. pays_actif persisté en DB
    if not selected_pays_id:
        pays_actif_id = getattr(request.user, "pays_actif_id", None)
        if pays_actif_id and Pays.objects.filter(id=pays_actif_id, afficher_au_dashboard=True).exists():
            selected_pays_id = pays_actif_id

    # 3. Affectation statique de l'employé
    if not selected_pays_id:
        user_pays = getattr(request.user, "pays", None)
        if user_pays:
            selected_pays_id = user_pays.id

    # Synchroniser la session
    if persist:
        if selected_pays_id:
            request.session["selected_pays_id"] = selected_pays_id
        else:
            request.session.pop("selected_pays_id", None)

    return selected_pays_id

# === Vue pour les codes NACE === #

class ListNaceCodesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "").strip()
        
        # Query de base
        queryset = SubCategoryNaceCode.objects.filter(
            active=True
        ).select_related('category')
        
        # Filtre par recherche
        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) |
                Q(libelle__icontains=search_query) |
                Q(category__libelle__icontains=search_query)
            )
        
        # Limiter les résultats
        queryset = queryset.order_by('code')[:50]
        
        # Sérialiser
        data = []
        for subcat in queryset:
            data.append({
                'id': subcat.id,
                'code': subcat.code,
                'libelle': subcat.libelle,
                'categorie': subcat.category.libelle if subcat.category else '',
                'poids': subcat.poids
            })
        
        return Response({
            "success": True,
            "results": data,
            "count": len(data)
        })

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
        selected_pays_id = _resolve_selected_pays_id(request)

        acheteur_list = Acheteur.objects.select_related(
            "pays", "ville", "province", "forme_juridique", "statut_entreprise"
        )
        if selected_pays_id:
            acheteur_list = acheteur_list.filter(pays_id=selected_pays_id)
        
        # Récupérer les paramètres de requête
        search_query = request.query_params.get("search", "").strip()
        try:
            page_number = int(request.query_params.get("page", 1))
        except (TypeError, ValueError):
            page_number = 1
        page_number = max(1, page_number)

        try:
            items_per_page = int(request.query_params.get("page_size", 10))
        except (TypeError, ValueError):
            items_per_page = 10
        items_per_page = max(1, min(items_per_page, 100))

        sort_field = request.query_params.get("sort", "nom")
        sort_dir = request.query_params.get("sort_dir", "asc")
        filter_type = request.query_params.get("filter", "all")
        
        # Appliquer le filtre
        now = timezone.now()
        if filter_type == "active":
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            acheteur_list = acheteur_list.filter(updated_at__gte=start_of_month)
        elif filter_type == "new":
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            acheteur_list = acheteur_list.filter(created_at__gte=start_of_week)
        
        # Appliquer la recherche
        if search_query:
            id_q = Q()
            try:
                id_q = Q(id=int(search_query))
            except (TypeError, ValueError):
                pass
            acheteur_list = acheteur_list.filter(
                id_q
                | Q(code__icontains=search_query)
                | Q(nom__icontains=search_query)
                | Q(sigle__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(numero_adresse__icontains=search_query)
                | Q(site_internet__icontains=search_query)
                | Q(rue_adresse__icontains=search_query)
                | Q(activite_principale__icontains=search_query)
                | Q(forme_juridique__libelle__icontains=search_query)
                | Q(statut_entreprise__libelle__icontains=search_query)
                | Q(pays__nom__icontains=search_query)
                | Q(province__nom__icontains=search_query)
                | Q(ville__nom__icontains=search_query)
            )
        
        # Appliquer le tri
        sort_mapping = {
            "code": "code",
            "nom": "nom",
            "sigle": "sigle",
            "ville": "ville__nom",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        resolved_sort = sort_mapping.get(sort_field, "nom")
        order_prefix = "-" if sort_dir == "desc" else ""
        acheteur_list = acheteur_list.order_by(f"{order_prefix}{resolved_sort}", "id")
        
        # Pagination
        paginator = Paginator(acheteur_list, items_per_page)
        acheteur_page = paginator.get_page(page_number)
        
        # Sérialisation
        serializer = AcheteurSerializer(acheteur_page, many=True, context={"request": request})
        
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": acheteur_page.has_next(),
            "previous": acheteur_page.has_previous(),
            "current_page": acheteur_page.number,
            "selected_pays_id": selected_pays_id,
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
        
        selected_pays_id = _resolve_selected_pays_id(request)
        
        # Construction de la requête optimisée
        acheteur_query = Acheteur.objects.select_related(
            'pays', 'ville', 'province',
            'forme_juridique', 'statut_entreprise'
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
        serializer = AcheteurSerializer(acheteur_page, many=True, context={"request": request})
        
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
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"=== ERREUR LORS DE LA SAUVEGARDE ===")
                    print(f"Type: {type(e)}")
                    print(f"Message: {str(e)}")
                    print(f"Traceback:\n{error_details}")
                    
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
            import traceback
            error_details = traceback.format_exc()
            print(f"=== ERREUR GLOBALE ===")
            print(f"Type: {type(e)}")
            print(f"Message: {str(e)}")
            print(f"Traceback:\n{error_details}")
            
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



class InitierAcheteurView(APIView):
    """Crée un acheteur minimal (étape 1) — seul le nom est requis.
    Les étapes suivantes utilisent PUT /api/editer-un-acheteur/{id}/ pour compléter."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from main.models import (
            CategorieEntreprise, FormeJuridique, StatutEntreprise
        )

        nom = (request.data.get('nom') or '').strip()
        if len(nom) < 2:
            return Response({
                "success": False,
                "message": "Le nom doit contenir au moins 2 caractères.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier unicité du nom
        if Acheteur.objects.filter(nom__iexact=nom).exists():
            return Response({
                "success": False,
                "message": f"Un acheteur avec le nom « {nom} » existe déjà.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Résoudre les FK optionnelles
        def resolve_fk(model, pk_val):
            if pk_val:
                try:
                    return model.objects.get(pk=int(pk_val))
                except (model.DoesNotExist, ValueError, TypeError):
                    pass
            return None

        try:
            acheteur = Acheteur.objects.create(
                nom=nom,
                sigle=(request.data.get('sigle') or '').strip(),
                description=(request.data.get('description') or '').strip(),
                activite_principale=(request.data.get('activite_principale') or '').strip(),
                date_creation=request.data.get('date_creation') or None,
                forme_juridique=resolve_fk(FormeJuridique, request.data.get('forme_juridique')),
                statut_entreprise=resolve_fk(StatutEntreprise, request.data.get('statut_entreprise')),
                created_by=request.user,
            )
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ACHETEUR_CREATED',
                    object_id=acheteur.id,
                    object_type='Acheteur',
                    details=f"Acheteur '{acheteur.nom}' initié par {request.user.username}",
                    ip_address=request.META.get('REMOTE_ADDR', '')
                )
            except Exception:
                pass  # log failure must not block creation

            return Response({
                "success": True,
                "message": "Acheteur créé. Complétez les étapes suivantes.",
                "acheteur_id": acheteur.id,
                "code": acheteur.code or '',
                "nom": acheteur.nom,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"InitierAcheteurView error: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Erreur lors de la création : {str(e)}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditAcheteurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, id):
        """Récupère l'acheteur ou retourne 404"""
        try:
            return Acheteur.objects.select_related(
                'pays', 'ville', 'province', 
                'forme_juridique', 'statut_entreprise'
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
        
        serializer = GetAcheteurSerializer(acheteur, context={"request": request})
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

                if request.data.get('creation_complete') is True or str(request.data.get('creation_complete')).lower() == 'true':
                    Acheteur.objects.filter(pk=instance.pk).update(creation_complete=True)
                    instance.refresh_from_db()

                # Serializer pour la réponse
                response_serializer = GetAcheteurSerializer(instance, context={"request": request})
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


class AcheteursIncompletView(APIView):
    """Retourne les acheteurs créés par l'utilisateur courant dont le wizard n'est pas terminé."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qs = Acheteur.objects.filter(
            created_by=request.user,
            creation_complete=False,
            ville__isnull=True,
        ).select_related('statut_entreprise').order_by('-created_at')[:50]

        data = []
        for a in qs:
            data.append({
                "id": a.id,
                "nom": a.nom,
                "code": a.code or '',
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

        return Response({"count": len(data), "acheteurs": data})


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
                'forme_juridique', 'statut_entreprise'
            ).get(id=id)
            
            serializer = GetAcheteurSerializer(acheteur, context={"request": request})
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
            selected_pays_id = _resolve_selected_pays_id(request)

            acheteurs = Acheteur.objects.all()
            if selected_pays_id:
                acheteurs = acheteurs.filter(pays_id=selected_pays_id)
            
            total_count = acheteurs.count()
            now = timezone.now()
            
            # Ce mois
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month = acheteurs.filter(created_at__gte=start_of_month).count()
            
            # Cette semaine (lundi à 00:00:00)
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            this_week = acheteurs.filter(created_at__gte=start_of_week).count()
            
            # Nom du pays actif (None = tous pays, le JS traduit via t('all_countries'))
            active_country = None
            if selected_pays_id:
                pays = Pays.objects.filter(id=selected_pays_id).first()
                if pays:
                    active_country = pays.nom

            stats = {
                'total': total_count,
                'thisMonth': this_month,
                'thisWeek': this_week,
                'activeCountry': active_country,
                'allCountries': active_country is None,
            }

            return Response(stats)
            
        except Exception as e:
            logger.exception("Erreur dans AcheteurStatsView: %s", str(e))
            
            return Response({
                'total': 0,
                'thisMonth': 0,
                'thisWeek': 0,
                'activeCountry': 'Erreur'
            }, status=200)
