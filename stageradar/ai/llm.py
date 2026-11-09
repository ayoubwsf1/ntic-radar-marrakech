# ==============================================================================
# Fichier : llm.py
# Rôle : Client universel pour communiquer avec un modèle de langage (LLM).
#        Supporte deux fournisseurs : OpenRouter (gratuit par défaut) ou Anthropic.
# ==============================================================================

# Permet d'utiliser les annotations de type modernes
from __future__ import annotations

# Bibliothèque pour envoyer des requêtes HTTP vers les APIs
import requests

# Importer le modèle par défaut, l'URL de l'API et la fonction de lecture des secrets
from ..config import LLM_MODEL, LLM_URL, get_secret


# ------------------------------------------------------------------------------
# Classe d'exception : LLMError
# Rôle : Signaler une erreur lors de l'appel à l'Intelligence Artificielle.
# ------------------------------------------------------------------------------
class LLMError(RuntimeError):
    pass


# ------------------------------------------------------------------------------
# Classe principale : LLMClient
# Rôle : Gérer la connexion et l'envoi de questions au modèle d'IA.
# ------------------------------------------------------------------------------
class LLMClient:
    # Constructeur de la classe
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: int = 60):
        # 1. Récupérer la clé API (OpenRouter en priorité, sinon Anthropic)
        self.api_key   = api_key or get_secret("OPENROUTER_API_KEY") or get_secret("ANTHROPIC_API_KEY")
        # 2. Déterminer quel fournisseur utiliser selon la clé disponible
        self._provider = "openrouter" if get_secret("OPENROUTER_API_KEY") else "anthropic"
        # 3. Définir le modèle d'IA à utiliser (par défaut Mistral 7B gratuit via OpenRouter)
        self.model     = model or LLM_MODEL
        # 4. Temps d'attente maximum pour la réponse de l'API (en secondes)
        self.timeout   = timeout

    # Propriété calculée : vérifier si une clé API est configurée
    @property
    def available(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------------------
    # Méthode principale : complete
    # Rôle : Envoyer une question (prompt) à l'IA et recevoir la réponse.
    # ------------------------------------------------------------------------------
    def complete(self, user: str, system: str = "", max_tokens: int = 1800, temperature: float = 0.3) -> str:
        # Vérifier qu'une clé API est bien présente
        if not self.available:
            raise LLMError("Aucune clé API configurée (OPENROUTER_API_KEY ou ANTHROPIC_API_KEY).")

        # Appeler la bonne API selon le fournisseur détecté
        if self._provider == "openrouter":
            return self._openrouter(user, system, max_tokens, temperature)
        return self._anthropic(user, system, max_tokens, temperature)

    # ==============================================================================
    # MÉTHODE INTERNE : _openrouter
    # Rôle : Envoyer la requête à OpenRouter (format compatible OpenAI).
    # ==============================================================================
    def _openrouter(self, user: str, system: str, max_tokens: int, temperature: float) -> str:
        # Construire la liste des messages (système + utilisateur)
        messages = []
        if system:
            # Le message système donne le contexte et les instructions générales
            messages.append({"role": "system", "content": system})
        # Le message utilisateur contient la question ou la tâche à réaliser
        messages.append({"role": "user", "content": user})

        try:
            # Envoyer la requête POST à OpenRouter
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json={
                    "model": self.model,                # Modèle d'IA (ex: mistralai/mistral-7b-instruct:free)
                    "messages": messages,               # Liste des messages
                    "max_tokens": max_tokens,           # Nombre maximum de mots dans la réponse
                    "temperature": temperature,         # Créativité (0 = précis, 1 = créatif)
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",   # Clé secrète d'authentification
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://ntic-radar.local",  # Identifiant du projet
                    "X-Title": "Ntic Radar CV Agent",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            # En cas de problème réseau (pas d'internet, serveur inaccessible...)
            raise LLMError(f"Erreur réseau : {str(e)[:120]}") from e

        # Vérifier que le serveur a bien répondu (code HTTP 200 = succès)
        if r.status_code != 200:
            raise LLMError(f"OpenRouter {r.status_code} : {r.text[:200]}")

        try:
            # Extraire le texte de la réponse de l'IA depuis le JSON
            return r.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            # Si la structure JSON ne correspond pas à ce qu'on attend
            raise LLMError(f"Réponse inattendue : {r.text[:200]}") from e

    # ==============================================================================
    # MÉTHODE INTERNE : _anthropic
    # Rôle : Envoyer la requête à l'API Anthropic (format natif Claude).
    # ==============================================================================
    def _anthropic(self, user: str, system: str, max_tokens: int, temperature: float) -> str:
        # Préparer le corps de la requête au format Anthropic
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        # Le système prompt est envoyé séparément chez Anthropic
        if system:
            body["system"] = system

        try:
            # Envoyer la requête POST à l'API Anthropic
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=body,
                headers={
                    "x-api-key": self.api_key,                 # Clé API Anthropic
                    "anthropic-version": "2023-06-01",         # Version de l'API
                    "content-type": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            # En cas de problème de connexion
            raise LLMError(f"Erreur réseau : {str(e)[:120]}") from e

        # Vérifier que la requête a réussi
        if r.status_code != 200:
            raise LLMError(f"Anthropic {r.status_code} : {r.text[:200]}")

        # Extraire les blocs de texte de la réponse JSON
        blocs = r.json().get("content", [])
        # Concaténer tous les morceaux de texte et renvoyer la réponse complète
        return "".join(b.get("text", "") for b in blocs if b.get("type") == "text").strip()


# ------------------------------------------------------------------------------
# Fonction utilitaire : get_client
# Rôle : Créer et retourner une instance prête à l'emploi du client LLM.
# ------------------------------------------------------------------------------
def get_client() -> LLMClient:
    return LLMClient()
