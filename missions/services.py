"""
Services métier pour le système de gestion des missions FUCEC
"""
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction
from .models import Mission, Validation, SignatureFinanciere, Notification
from users.models import User

logger = logging.getLogger(__name__)


class ValidationService:
    """Service pour gérer le workflow de validation des missions"""

    @staticmethod
    def initiate_workflow(mission):
        """
        Initie le workflow de validation selon les règles métier
        """
        # Règles de validation selon budget et durée
        budget = mission.budget_estime
        duree = mission.duree

        validations = []

        # Toujours N+1 (Chef d'agence)
        validations.append(ValidationService._create_validation(
            mission, 'CHEF_AGENCE', 1, 24
        ))

        # N+2 si budget > 300K ou durée > 3 jours
        if budget > 300000 or duree > 3:
            validations.append(ValidationService._create_validation(
                mission, 'RESPONSABLE_COPEC', 2, 48
            ))

        # DG si budget > 1M ou durée > 7 jours
        if budget > 1000000 or duree > 7:
            validations.append(ValidationService._create_validation(
                mission, 'DG', 3, 72
            ))

        # Sauvegarder les validations
        for validation in validations:
            validation.save()

        # Changer le statut de la mission
        mission.statut = 'EN_ATTENTE'
        mission.save()

        # Notifier le premier valideur
        if validations:
            NotificationService.notify_validation_required(validations[0])

        return validations

    @staticmethod
    def _create_validation(mission, niveau, ordre, delai_heures):
        """Crée une validation pour un niveau donné"""
        # Trouver le valideur approprié selon la hiérarchie
        valideur = ValidationService._find_valideur(mission, niveau)

        # Calculer la date d'échéance
        date_echeance = timezone.now() + timezone.timedelta(hours=delai_heures)

        return Validation(
            mission=mission,
            niveau=niveau,
            valideur=valideur,
            ordre=ordre,
            delai_heures=delai_heures,
            date_echeance=date_echeance
        )

    @staticmethod
    def _find_valideur(mission, niveau):
        """Trouve le valideur approprié selon le niveau"""
        createur = mission.createur

        if niveau == 'CHEF_AGENCE':
            # Le manager direct du créateur
            return createur.manager or createur
        elif niveau == 'RESPONSABLE_COPEC':
            # Responsable de l'entité
            return mission.entite.responsable or createur
        elif niveau == 'DG':
            # DG du système (premier user avec rôle DG)
            return User.objects.filter(role='DG').first() or createur

        return createur

    @staticmethod
    def process_decision(validation, decision, commentaire=""):
        """
        Traite une décision de validation
        """
        with transaction.atomic():
            # Mettre à jour la validation
            validation.statut = decision
            validation.commentaire = commentaire
            validation.date_validation = timezone.now()
            validation.save()

            mission = validation.mission

            if decision == 'VALIDEE':
                # Vérifier s'il reste des validations
                next_validation = Validation.objects.filter(
                    mission=mission,
                    ordre__gt=validation.ordre,
                    statut='EN_ATTENTE'
                ).order_by('ordre').first()

                if next_validation:
                    # Notifier le prochain valideur
                    NotificationService.notify_validation_required(next_validation)
                else:
                    # Toutes les validations sont passées - approuver la mission
                    ValidationService._approve_mission(mission)

            elif decision == 'REJETEE':
                # Rejeter la mission
                mission.statut = 'REJETEE'
                mission.save()
                NotificationService.notify_mission_rejected(mission, validation)

        return validation

    @staticmethod
    def _approve_mission(mission):
        """Approuve définitivement la mission"""
        mission.statut = 'VALIDEE'
        mission.save()

        # Générer l'ordre de mission PDF
        PDFService.generate_ordre_mission(mission)

        # Initier le workflow de signatures
        SignatureService.initiate_workflow(mission)

        # Notifier l'agent
        NotificationService.notify_mission_validated(mission)


class SignatureService:
    """Service pour gérer le workflow de signatures financières"""

    @staticmethod
    def initiate_workflow(mission):
        """Initie le workflow de signatures financières"""
        signatures = []

        # Signature de l'agent (ordre 1)
        signatures.append(SignatureFinanciere(
            mission=mission,
            niveau='AGENT',
            signataire=mission.createur,
            ordre=1
        ))

        # Signature N+1 (Chef d'agence) (ordre 2)
        n1 = mission.createur.manager
        if n1:
            signatures.append(SignatureFinanciere(
                mission=mission,
                niveau='CHEF_AGENCE',
                signataire=n1,
                ordre=2
            ))

        # Signature Directeur Finances (ordre 3)
        df = User.objects.filter(role='DIRECTEUR_FINANCES').first()
        if df:
            signatures.append(SignatureFinanciere(
                mission=mission,
                niveau='DIRECTEUR_FINANCES',
                signataire=df,
                ordre=3
            ))

        # Sauvegarder les signatures
        for signature in signatures:
            signature.save()

        # Notifier le premier signataire (l'agent)
        if signatures:
            NotificationService.notify_signature_required(signatures[0])

    @staticmethod
    def process_signature(signature_financiere):
        """Traite une signature financière avec workflow séquentiel"""
        from .models import SignatureFinanciere

        with transaction.atomic():
            signature_financiere.statut = 'SIGNE'
            signature_financiere.date_signature = timezone.now()
            signature_financiere.save()

            mission = signature_financiere.mission

            # Vérifier si toutes les signatures sont complètes
            signatures_total = SignatureFinanciere.objects.filter(mission=mission).count()
            signatures_completees = SignatureFinanciere.objects.filter(
                mission=mission, statut='SIGNE'
            ).count()

            if signatures_completees < signatures_total:
                # Il reste des signatures - notifier la suivante
                next_signature = SignatureFinanciere.objects.filter(
                    mission=mission,
                    ordre__gt=signature_financiere.ordre,
                    statut='EN_ATTENTE'
                ).order_by('ordre').first()

                if next_signature:
                    NotificationService.notify_signature_required(next_signature)
            else:
                # Toutes les signatures sont complètes
                SignatureService._complete_signatures(mission)

    @staticmethod
    def _complete_signatures(mission):
        """Finalise le processus de signatures"""
        mission.signatures_completes = True
        mission.save()

        # Notifier le comptable pour le déblocage
        NotificationService.notify_payment_authorized(mission)


class NotificationService:
    """Service pour gérer les notifications"""

    @staticmethod
    def notify_validation_required(validation):
        """Notifie qu'une validation est requise"""
        titre = f"Validation requise - Mission {validation.mission.reference}"
        message = f"Une validation est requise pour la mission {validation.mission.titre}"

        NotificationService._create_notification(
            validation.valideur,
            titre,
            message,
            'VALIDATION',
            f'/missions/{validation.mission.id}'
        )

        # Envoyer email
        EmailService.send_validation_notification(validation)

    @staticmethod
    def notify_mission_validated(mission):
        """Notifie que la mission est validée"""
        titre = f"Mission validée - {mission.reference}"
        message = f"Votre mission {mission.titre} a été validée et approuvée."

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'APPROBATION'
        )

        EmailService.send_mission_validated_notification(mission)

    @staticmethod
    def notify_mission_rejected(mission, validation):
        """Notifie que la mission est rejetée"""
        titre = f"Mission rejetée - {mission.reference}"
        message = f"Votre mission {mission.titre} a été rejetée."

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'REJET'
        )

        EmailService.send_mission_rejected_notification(mission, validation)

    @staticmethod
    def notify_signature_required(signature):
        """Notifie qu'une signature est requise"""
        titre = f"Signature requise - Mission {signature.mission.reference}"
        message = f"Votre signature est requise pour la mission {signature.mission.titre}"

        NotificationService._create_notification(
            signature.signataire,
            titre,
            message,
            'VALIDATION',
            f'/missions/{signature.mission.id}/sign'
        )

        EmailService.send_signature_notification(signature)

    @staticmethod
    def notify_mission_ready(mission):
        """Notifie que la mission est prête avec toutes les signatures"""
        titre = f"Mission prête - {mission.reference}"
        message = f"Votre mission {mission.titre} est maintenant complète et prête."

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'INFO'
        )

    @staticmethod
    def notify_payment_authorized(mission):
        """Notifie que le paiement est autorisé (toutes signatures obtenues)"""
        titre = f"Déblocage autorisé - Mission {mission.reference}"
        message = f"Le déblocage des fonds est autorisé pour la mission {mission.titre}"

        # Notifier tous les comptables
        comptables = User.objects.filter(role='COMPTABLE')
        for comptable in comptables:
            NotificationService._create_notification(
                comptable,
                titre,
                message,
                'VALIDATION'
            )
            EmailService.send_payment_authorized_notification(mission, comptable)

    @staticmethod
    def notify_payment_made(mission, avance):
        """Notifie qu'un paiement a été effectué"""
        titre = f"Avance versée - Mission {mission.reference}"
        message = f"Une avance de {avance.montant} FCFA a été versée pour votre mission {mission.titre}"

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'INFO'
        )

        EmailService.send_payment_made_notification(mission, avance)

    @staticmethod
    def notify_return_declared(mission):
        """Notifie que l'agent a déclaré son retour"""
        titre = f"Retour de mission déclaré - {mission.reference}"
        message = f"L'agent {mission.createur.get_full_name()} a déclaré son retour de mission {mission.titre}"

        # Notifier RH
        rh_users = User.objects.filter(role='RH')
        for rh in rh_users:
            NotificationService._create_notification(
                rh,
                titre,
                message,
                'INFO'
            )
            EmailService.send_return_declared_notification(mission, rh)

    @staticmethod
    def notify_justificatifs_submitted(mission):
        """Notifie que les justificatifs ont été déposés"""
        titre = f"Justificatifs déposés - {mission.reference}"
        message = f"Les justificatifs de mission {mission.titre} ont été déposés par l'agent"

        # Notifier RH
        rh_users = User.objects.filter(role='RH')
        for rh in rh_users:
            NotificationService._create_notification(
                rh,
                titre,
                message,
                'VALIDATION'
            )
            EmailService.send_justificatifs_submitted_notification(mission, rh)

    @staticmethod
    def notify_justificatifs_rejected(mission, commentaire):
        """Notifie que les justificatifs ont été rejetés"""
        titre = f"Justificatifs rejetés - {mission.reference}"
        message = f"Vos justificatifs pour la mission {mission.titre} ont été rejetés. {commentaire}"

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'REJET'
        )
        EmailService.send_justificatifs_rejected_notification(mission, commentaire)

    @staticmethod
    def notify_fucec_refund(mission, montant):
        """Notifie que FUCEC doit rembourser l'agent"""
        titre = f"Remboursement FUCEC - {mission.reference}"
        message = f"FUCEC doit vous rembourser {montant} FCFA pour la mission {mission.titre}"

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'INFO'
        )
        EmailService.send_fucec_refund_notification(mission, montant)

    @staticmethod
    def notify_agent_refund(mission, montant):
        """Notifie que l'agent doit rembourser FUCEC"""
        titre = f"Remboursement agent - {mission.reference}"
        message = f"Vous devez rembourser {montant} FCFA à FUCEC pour la mission {mission.titre}"

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'VALIDATION'
        )
        EmailService.send_agent_refund_notification(mission, montant)

    @staticmethod
    def notify_mission_balanced(mission):
        """Notifie que la mission est équilibrée"""
        titre = f"Mission équilibrée - {mission.reference}"
        message = f"La mission {mission.titre} est équilibrée (dépenses = avances)"

        NotificationService._create_notification(
            mission.createur,
            titre,
            message,
            'INFO'
        )
        EmailService.send_mission_balanced_notification(mission)

    @staticmethod
    def _create_notification(destinataire, titre, message, type_notif, lien=""):
        """Crée une notification en base"""
        Notification.objects.create(
            destinataire=destinataire,
            titre=titre,
            message=message,
            type=type_notif,
            lien=lien
        )


class EmailService:
    """Service pour l'envoi d'emails"""

    @staticmethod
    def send_validation_notification(validation):
        """Envoie un email de notification de validation"""
        subject = f"Validation requise - Mission {validation.mission.reference}"
        context = {
            'validation': validation,
            'mission': validation.mission,
            'valideur': validation.valideur,
        }

        html_message = f"""
        <h2>Validation requise</h2>
        <p>Une validation est requise pour la mission <strong>{validation.mission.titre}</strong></p>
        <p>Référence: {validation.mission.reference}</p>
        <p>Budget estimé: {validation.mission.budget_estime} FCFA</p>
        <p>Créateur: {validation.mission.createur.get_full_name()}</p>
        <p>Date limite: {validation.date_echeance}</p>
        """
        plain_message = f"""
        Validation requise

        Une validation est requise pour la mission {validation.mission.titre}
        Référence: {validation.mission.reference}
        Budget estimé: {validation.mission.budget_estime} FCFA
        Créateur: {validation.mission.createur.get_full_name()}
        Date limite: {validation.date_echeance}
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [validation.valideur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_mission_validated_notification(mission):
        """Envoie un email de mission validée"""
        subject = f"Mission validée - {mission.reference}"
        context = {'mission': mission}

        html_message = f"""
        <h2>Mission validée</h2>
        <p>Votre mission <strong>{mission.titre}</strong> a été validée et approuvée.</p>
        <p>Référence: {mission.reference}</p>
        <p>Vous allez recevoir les instructions pour les signatures financières.</p>
        """
        plain_message = f"""
        Mission validée

        Votre mission {mission.titre} a été validée et approuvée.
        Référence: {mission.reference}
        Vous allez recevoir les instructions pour les signatures financières.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_mission_rejected_notification(mission, validation):
        """Envoie un email de mission rejetée"""
        subject = f"Mission rejetée - {mission.reference}"
        context = {
            'mission': mission,
            'validation': validation,
        }

        html_message = f"""
        <h2>Mission rejetée</h2>
        <p>Votre mission <strong>{mission.titre}</strong> a été rejetée.</p>
        <p>Référence: {mission.reference}</p>
        <p>Motif: {validation.commentaire or 'Non spécifié'}</p>
        """
        plain_message = f"""
        Mission rejetée

        Votre mission {mission.titre} a été rejetée.
        Référence: {mission.reference}
        Motif: {validation.commentaire or 'Non spécifié'}
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_signature_notification(signature):
        """Envoie un email de notification de signature"""
        subject = f"Signature requise - Mission {signature.mission.reference}"
        context = {
            'signature': signature,
            'mission': signature.mission,
        }

        html_message = f"""
        <h2>Signature requise</h2>
        <p>Votre signature est requise pour la mission <strong>{signature.mission.titre}</strong></p>
        <p>Référence: {signature.mission.reference}</p>
        <p>Niveau: {signature.niveau}</p>
        """
        plain_message = f"""
        Signature requise

        Votre signature est requise pour la mission {signature.mission.titre}
        Référence: {signature.mission.reference}
        Niveau: {signature.niveau}
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [signature.signataire.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_payment_authorized_notification(mission, comptable):
        """Envoie un email de déblocage autorisé"""
        subject = f"Déblocage autorisé - Mission {mission.reference}"
        context = {
            'mission': mission,
            'comptable': comptable,
        }

        html_message = f"""
        <h2>Déblocage autorisé</h2>
        <p>Le déblocage des fonds est autorisé pour la mission <strong>{mission.titre}</strong></p>
        <p>Référence: {mission.reference}</p>
        <p>Budget approuvé: {mission.budget_estime} FCFA</p>
        """
        plain_message = f"""
        Déblocage autorisé

        Le déblocage des fonds est autorisé pour la mission {mission.titre}
        Référence: {mission.reference}
        Budget approuvé: {mission.budget_estime} FCFA
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [comptable.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_payment_made_notification(mission, avance):
        """Envoie un email de paiement effectué"""
        subject = f"Avance versée - Mission {mission.reference}"
        context = {
            'mission': mission,
            'avance': avance,
        }

        html_message = f"""
        <h2>Avance versée</h2>
        <p>Une avance de <strong>{avance.montant} FCFA</strong> a été versée pour votre mission.</p>
        <p>Mission: {mission.titre}</p>
        <p>Référence: {mission.reference}</p>
        <p>Mode de versement: {avance.mode_versement}</p>
        """
        plain_message = f"""
        Avance versée

        Une avance de {avance.montant} FCFA a été versée pour votre mission.
        Mission: {mission.titre}
        Référence: {mission.reference}
        Mode de versement: {avance.mode_versement}
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_return_declared_notification(mission, rh):
        """Envoie un email de retour déclaré"""
        subject = f"Retour de mission déclaré - {mission.reference}"
        context = {'mission': mission, 'rh': rh}

        html_message = f"""
        <h2>Retour de mission déclaré</h2>
        <p>L'agent <strong>{mission.createur.get_full_name()}</strong> a déclaré son retour de mission.</p>
        <p>Mission: {mission.titre}</p>
        <p>Référence: {mission.reference}</p>
        <p>Date de retour: {mission.date_retour_reelle}</p>
        <p>L'agent a 72h pour déposer ses justificatifs.</p>
        """
        plain_message = f"""
        Retour de mission déclaré

        L'agent {mission.createur.get_full_name()} a déclaré son retour de mission.
        Mission: {mission.titre}
        Référence: {mission.reference}
        Date de retour: {mission.date_retour_reelle}
        L'agent a 72h pour déposer ses justificatifs.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [rh.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_justificatifs_submitted_notification(mission, rh):
        """Envoie un email de justificatifs déposés"""
        subject = f"Justificatifs déposés - {mission.reference}"
        context = {'mission': mission, 'rh': rh}

        html_message = f"""
        <h2>Justificatifs déposés</h2>
        <p>L'agent <strong>{mission.createur.get_full_name()}</strong> a déposé ses justificatifs de mission.</p>
        <p>Mission: {mission.titre}</p>
        <p>Référence: {mission.reference}</p>
        <p>Veuillez procéder à la vérification des justificatifs.</p>
        """
        plain_message = f"""
        Justificatifs déposés

        L'agent {mission.createur.get_full_name()} a déposé ses justificatifs de mission.
        Mission: {mission.titre}
        Référence: {mission.reference}
        Veuillez procéder à la vérification des justificatifs.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [rh.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_justificatifs_rejected_notification(mission, commentaire):
        """Envoie un email de justificatifs rejetés"""
        subject = f"Justificatifs rejetés - {mission.reference}"
        context = {'mission': mission}

        html_message = f"""
        <h2>Justificatifs rejetés</h2>
        <p>Vos justificatifs pour la mission <strong>{mission.titre}</strong> ont été rejetés.</p>
        <p>Référence: {mission.reference}</p>
        <p>Motif: {commentaire}</p>
        <p>Veuillez corriger et redéposer vos justificatifs.</p>
        """
        plain_message = f"""
        Justificatifs rejetés

        Vos justificatifs pour la mission {mission.titre} ont été rejetés.
        Référence: {mission.reference}
        Motif: {commentaire}
        Veuillez corriger et redéposer vos justificatifs.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_fucec_refund_notification(mission, montant):
        """Envoie un email de remboursement FUCEC"""
        subject = f"Remboursement FUCEC - {mission.reference}"
        context = {'mission': mission, 'montant': montant}

        html_message = f"""
        <h2>Remboursement FUCEC</h2>
        <p>FUCEC doit vous rembourser <strong>{montant} FCFA</strong> pour la mission <strong>{mission.titre}</strong>.</p>
        <p>Référence: {mission.reference}</p>
        <p>Le remboursement sera effectué dans les prochains jours.</p>
        """
        plain_message = f"""
        Remboursement FUCEC

        FUCEC doit vous rembourser {montant} FCFA pour la mission {mission.titre}.
        Référence: {mission.reference}
        Le remboursement sera effectué dans les prochains jours.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_agent_refund_notification(mission, montant):
        """Envoie un email de remboursement agent"""
        subject = f"Remboursement agent - {mission.reference}"
        context = {'mission': mission, 'montant': montant}

        html_message = f"""
        <h2>Remboursement requis</h2>
        <p>Vous devez rembourser <strong>{montant} FCFA</strong> à FUCEC pour la mission <strong>{mission.titre}</strong>.</p>
        <p>Référence: {mission.reference}</p>
        <p>Veuillez procéder au remboursement dans les plus brefs délais.</p>
        """
        plain_message = f"""
        Remboursement requis

        Vous devez rembourser {montant} FCFA à FUCEC pour la mission {mission.titre}.
        Référence: {mission.reference}
        Veuillez procéder au remboursement dans les plus brefs délais.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

    @staticmethod
    def send_mission_balanced_notification(mission):
        """Envoie un email de mission équilibrée"""
        subject = f"Mission équilibrée - {mission.reference}"
        context = {'mission': mission}

        html_message = f"""
        <h2>Mission équilibrée</h2>
        <p>La mission <strong>{mission.titre}</strong> est équilibrée.</p>
        <p>Référence: {mission.reference}</p>
        <p>Les dépenses correspondent exactement aux avances versées.</p>
        """
        plain_message = f"""
        Mission équilibrée

        La mission {mission.titre} est équilibrée.
        Référence: {mission.reference}
        Les dépenses correspondent exactement aux avances versées.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )


class TimerService:
    """Service pour gérer les timers et relances automatiques"""

    @staticmethod
    def set_signature_deadline(signature_financiere):
        """Définit la date limite de signature (72h)"""
        if not signature_financiere.date_limite_signature:
            signature_financiere.date_limite_signature = timezone.now() + timezone.timedelta(hours=72)
            signature_financiere.save()

    @staticmethod
    def set_justificatifs_deadline(mission):
        """Définit la date limite pour les justificatifs (72h après retour)"""
        if mission.date_retour_reelle and not mission.date_limite_justificatifs:
            mission.date_limite_justificatifs = mission.date_retour_reelle + timezone.timedelta(hours=72)
            mission.save()

    @staticmethod
    def check_overdue_signatures():
        """Vérifie les signatures en retard et envoie des relances"""
        from .models import SignatureFinanciere

        overdue_signatures = SignatureFinanciere.objects.filter(
            statut='EN_ATTENTE',
            date_limite_signature__lt=timezone.now(),
            relance_effectuee=False
        )

        for signature in overdue_signatures:
            TimerService.send_signature_reminder(signature)

    @staticmethod
    def check_overdue_justificatifs():
        """Vérifie les missions avec justificatifs en retard"""
        from .models import Mission

        overdue_missions = Mission.objects.filter(
            retour_declare=True,
            justificatifs_deposes=False,
            date_limite_justificatifs__lt=timezone.now()
        )

        for mission in overdue_missions:
            # Vérifier si ça fait 7 jours qu'on n'a pas eu de justificatifs
            if not mission.date_derniere_relance_justificatifs:
                days_overdue = (timezone.now() - mission.date_limite_justificatifs).days
                if days_overdue >= 7:
                    TimerService.escalate_to_n1(mission)
                elif not mission.relance_justificatifs:
                    TimerService.send_justificatifs_reminder(mission)
            elif (timezone.now() - mission.date_derniere_relance_justificatifs).days >= 7:
                TimerService.escalate_to_n1(mission)

    @staticmethod
    def check_missions_to_archive():
        """Vérifie les missions à archiver (60j après clôture)"""
        from .models import Mission

        missions_to_archive = Mission.objects.filter(
            cloturee=True,
            archivee=False,
            date_cloture__lt=timezone.now() - timezone.timedelta(days=60)
        )

        for mission in missions_to_archive:
            TimerService.archive_mission(mission)

    @staticmethod
    def send_signature_reminder(signature):
        """Envoie une relance pour une signature en retard"""
        subject = f"RAPPEL: Signature requise - Mission {signature.mission.reference}"
        context = {'signature': signature, 'mission': signature.mission}

        html_message = f"""
        <h2>Rappel de signature</h2>
        <p>Vous avez une signature en attente pour la mission <strong>{signature.mission.titre}</strong></p>
        <p>Référence: {signature.mission.reference}</p>
        <p>Niveau: {signature.niveau}</p>
        <p><strong>Cette signature était attendue avant le {signature.date_limite_signature}</strong></p>
        <p>Veuillez procéder à la signature dans les plus brefs délais.</p>
        """
        plain_message = f"""
        Rappel de signature

        Vous avez une signature en attente pour la mission {signature.mission.titre}
        Référence: {signature.mission.reference}
        Niveau: {signature.niveau}
        Cette signature était attendue avant le {signature.date_limite_signature}

        Veuillez procéder à la signature dans les plus brefs délais.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [signature.signataire.email],
            html_message=html_message,
            fail_silently=True
        )

        # Marquer la relance comme effectuée
        signature.relance_effectuee = True
        signature.date_derniere_relance = timezone.now()
        signature.save()

    @staticmethod
    def send_justificatifs_reminder(mission):
        """Envoie une relance pour les justificatifs"""
        subject = f"RAPPEL: Dépôt des justificatifs - Mission {mission.reference}"
        context = {'mission': mission}

        html_message = f"""
        <h2>Rappel: Dépôt des justificatifs</h2>
        <p>La date limite pour déposer vos justificatifs de mission approche.</p>
        <p>Mission: <strong>{mission.titre}</strong></p>
        <p>Référence: {mission.reference}</p>
        <p>Date limite: {mission.date_limite_justificatifs}</p>
        <p>Veuillez déposer vos justificatifs dans les plus brefs délais.</p>
        """
        plain_message = f"""
        Rappel: Dépôt des justificatifs

        La date limite pour déposer vos justificatifs de mission approche.
        Mission: {mission.titre}
        Référence: {mission.reference}
        Date limite: {mission.date_limite_justificatifs}

        Veuillez déposer vos justificatifs dans les plus brefs délais.
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [mission.createur.email],
            html_message=html_message,
            fail_silently=True
        )

        # Marquer la relance comme effectuée
        mission.relance_justificatifs = True
        mission.date_derniere_relance_justificatifs = timezone.now()
        mission.save()

    @staticmethod
    def escalate_to_n1(mission):
        """Escalade vers N+1 quand les justificatifs sont en retard de 7j"""
        n1 = mission.createur.manager
        if n1:
            subject = f"ESCALADE: Justificatifs en retard - Mission {mission.reference}"

            html_message = f"""
            <h2>Escalade: Justificatifs en retard</h2>
            <p>L'agent {mission.createur.get_full_name()} n'a toujours pas déposé ses justificatifs.</p>
            <p>Mission: <strong>{mission.titre}</strong></p>
            <p>Référence: {mission.reference}</p>
            <p>Date de retour: {mission.date_retour_reelle}</p>
            <p>Délai dépassé depuis: {(timezone.now() - mission.date_limite_justificatifs).days} jours</p>
            """
            plain_message = f"""
            Escalade: Justificatifs en retard

            L'agent {mission.createur.get_full_name()} n'a toujours pas déposé ses justificatifs.
            Mission: {mission.titre}
            Référence: {mission.reference}
            Date de retour: {mission.date_retour_reelle}
            Délai dépassé depuis: {(timezone.now() - mission.date_limite_justificatifs).days} jours
            """

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [n1.email],
                html_message=html_message,
                fail_silently=True
            )

    @staticmethod
    def archive_mission(mission):
        """Archive automatiquement une mission clôturée depuis 60j"""
        mission.archivee = True
        mission.date_archivage = timezone.now()
        mission.save()

        logger.info(f"Mission {mission.reference} archivée automatiquement")


class MissionReturnService:
    """Service pour gérer le workflow de retour de mission"""

    @staticmethod
    def declare_return(mission, agent):
        """L'agent déclare son retour de mission"""
        if mission.createur != agent:
            raise ValueError("Seul l'agent de la mission peut déclarer le retour")

        if mission.statut != 'EN_COURS':
            raise ValueError("La mission doit être en cours pour déclarer un retour")

        with transaction.atomic():
            mission.date_retour_reelle = timezone.now()
            mission.retour_declare = True
            mission.statut = 'RETOUR'  # Nouveau statut

            # Définir la date limite pour les justificatifs (72h)
            mission.date_limite_justificatifs = timezone.now() + timezone.timedelta(hours=72)

            mission.save()

            # Notifier l'agent et RH
            NotificationService.notify_return_declared(mission)

            return mission

    @staticmethod
    def submit_justificatifs(mission, justificatifs_data):
        """Agent dépose ses justificatifs"""
        # Ici nous aurions la logique pour traiter les justificatifs uploadés
        # Pour l'instant, on marque simplement comme déposés
        mission.justificatifs_deposes = True
        mission.save()

        # Notifier RH pour vérification
        NotificationService.notify_justificatifs_submitted(mission)

        return mission

    @staticmethod
    def verify_justificatifs(mission, verifier, decision, commentaire=""):
        """RH vérifie les justificatifs"""
        with transaction.atomic():
            if decision == 'APPROUVE':
                mission.justificatifs_verifies = True

                # Calculer le solde
                MissionReturnService.calculate_balance(mission)

                # Clôturer la mission
                MissionReturnService.close_mission(mission)

            elif decision == 'REJETTE':
                mission.justificatifs_deposes = False  # Permettre de redéposer
                NotificationService.notify_justificatifs_rejected(mission, commentaire)

            mission.save()

    @staticmethod
    def calculate_balance(mission):
        """Calcule le solde final de la mission"""
        from .models import Depense, Avance

        # Total des dépenses déclarées
        total_depenses = Depense.objects.filter(mission=mission).aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        # Total des avances versées
        total_avances = Avance.objects.filter(
            mission=mission,
            statut='VERSEEE'
        ).aggregate(total=models.Sum('montant'))['total'] or 0

        # Solde = Dépenses - Avances
        # Positif = FUCEC doit rembourser l'agent
        # Négatif = Agent doit rembourser FUCEC
        mission.solde_calcule = total_depenses - total_avances
        mission.save()

        return mission.solde_calcule

    @staticmethod
    def close_mission(mission):
        """Clôture la mission"""
        mission.cloturee = True
        mission.date_cloture = timezone.now()
        mission.statut = 'CLOTUREE'
        mission.save()

        # Notifier selon le solde
        if mission.solde_calcule > 0:
            NotificationService.notify_fucec_refund(mission, mission.solde_calcule)
        elif mission.solde_calcule < 0:
            NotificationService.notify_agent_refund(mission, abs(mission.solde_calcule))
        else:
            NotificationService.notify_mission_balanced(mission)


class PDFService:
    """Service pour générer les PDFs"""

    @staticmethod
    def generate_ordre_mission(mission):
        """
        Génère l'ordre de mission en PDF
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from io import BytesIO
            from django.core.files.base import ContentFile

            # Créer le buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Titre
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Centré
            )
            story.append(Paragraph("ORDRE DE MISSION", title_style))
            story.append(Spacer(1, 12))

            # Informations de la mission
            info_style = styles['Normal']

            mission_data = [
                ["Référence:", mission.reference],
                ["Titre:", mission.titre],
                ["Agent:", mission.createur.get_full_name()],
                ["Entité:", mission.entite.nom if mission.entite else "N/A"],
                ["Période:", f"Du {mission.date_debut} au {mission.date_fin}"],
                ["Lieu:", mission.lieu_mission],
                ["Budget estimé:", f"{mission.budget_estime:,.0f} FCFA"],
                ["Objet:", mission.description or "N/A"],
            ]

            # Créer la table
            table = Table(mission_data, colWidths=[100, 300])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
            story.append(Spacer(1, 20))

            # Participants
            if mission.participants.exists():
                story.append(Paragraph("Participants:", styles['Heading3']))
                participants = [p.get_full_name() for p in mission.participants.all()]
                story.append(Paragraph(", ".join(participants), info_style))
                story.append(Spacer(1, 12))

            # Véhicule
            if mission.vehicule:
                story.append(Paragraph("Véhicule:", styles['Heading3']))
                story.append(Paragraph(
                    f"{mission.vehicule.marque} {mission.vehicule.modele} - {mission.vehicule.immatriculation}",
                    info_style
                ))
                story.append(Spacer(1, 12))

            # Générer le PDF
            doc.build(story)

            # Sauvegarder dans la mission (on pourrait créer un champ fichier dans Mission)
            pdf_content = buffer.getvalue()
            buffer.close()

            # Pour l'exemple, on sauvegarde comme fichier temporaire
            # En production, il faudrait ajouter un champ FileField à Mission
            filename = f"ordre_mission_{mission.reference}.pdf"

            # Log de génération réussie
            logger.info(f"PDF généré pour la mission {mission.reference}")

            return pdf_content, filename

        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF pour la mission {mission.reference}: {str(e)}")
            return None, None
