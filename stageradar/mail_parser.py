# ==============================================================================
# Fichier : mail_parser.py
# Rôle : Décoder et analyser la structure brute d'un e-mail (octets / RFC 822)
#        pour en extraire proprement : l'expéditeur, l'objet, la date et le corps du texte.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Bibliothèque standard de traitement des e-mails en Python
import email
import email.policy
# Outil pour créer des structures de données simples
from dataclasses import dataclass
# Outils pour manipuler les dates et les fuseaux horaires (UTC)
from datetime import datetime, timezone
# Outils pour décoder les en-têtes d'e-mails contenant des caractères accentués
from email.header import decode_header, make_header
# Outils pour extraire les adresses e-mail et convertir les dates au format standard
from email.utils import getaddresses, parsedate_to_datetime

# Importer la fonction qui convertit du HTML en texte brut
from .text_utils import html_to_text


# ------------------------------------------------------------------------------
# Classe : Parsed
# Rôle : Représenter les informations essentielles d'un e-mail propre.
# ------------------------------------------------------------------------------
@dataclass
class Parsed:
    subject: str                  # Objet du message
    from_name: str                # Nom complet de l'expéditeur (ex: "Société X")
    from_addrs: list              # Liste des adresses e-mail de l'expéditeur
    to_addrs: list                # Liste des adresses e-mail des destinataires
    date: datetime                # Date d'envoi/réception
    body: str                     # Corps du message en texte lisible
    multipart_mixed: bool         # Vrai si l'e-mail contient des pièces jointes


# ------------------------------------------------------------------------------
# Fonction interne : _decode
# Rôle : Décoder un texte d'en-tête e-mail encodé en base64 ou quoted-printable.
# ------------------------------------------------------------------------------
def _decode(s) -> str:
    s = str(s or "")
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


# ------------------------------------------------------------------------------
# Fonction principale : parse_message
# Rôle : Transformer les octets bruts reçus du serveur IMAP en un objet Parsed propre.
# ------------------------------------------------------------------------------
def parse_message(header: bytes, text: bytes = b"") -> Parsed:
    # 1. Reconstituer le message complet (en-têtes + séparateur vide + corps)
    raw = header.rstrip(b"\r\n") + b"\r\n\r\n" + (text or b"")
    msg = email.message_from_bytes(raw, policy=email.policy.default)

    plain, html = "", ""
    # 2. Parcourir toutes les sous-parties du message (texte simple ou HTML)
    for part in msg.walk():
        ctype = part.get_content_type()
        # Ignorer les conteneurs multipart et tout ce qui n'est pas du texte
        if part.is_multipart() or ctype not in ("text/plain", "text/html"):
            continue
        try:
            # Récupérer et décoder les octets du texte
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="replace")
        except Exception:
            continue
        # Séparer le texte brut et le code HTML
        if ctype == "text/plain":
            plain += content
        else:
            html += content

    # 3. Utiliser le texte brut en priorité, sinon convertir le HTML en texte propre
    body = plain or html_to_text(html)

    # 4. Extraire les adresses d'expédition (From) et de réception (To, Cc)
    from_pairs = getaddresses([_decode(msg.get("From", ""))])
    to_pairs = getaddresses([_decode(msg.get("To", "")), _decode(msg.get("Cc", ""))])

    # 5. Analyser la date du message
    try:
        d = parsedate_to_datetime(str(msg.get("Date")))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
    except Exception:
        d = datetime.now(timezone.utc)

    # 6. Renvoyer l'objet Parsed avec toutes les données nettoyées
    return Parsed(
        subject=_decode(msg.get("Subject", "")),
        from_name=from_pairs[0][0] if from_pairs else "",
        from_addrs=[a.lower() for _, a in from_pairs if a],
        to_addrs=[a.lower() for _, a in to_pairs if a],
        date=d,
        body=body,
        multipart_mixed=msg.get_content_type() == "multipart/mixed",
    )
