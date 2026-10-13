# Consultation à réaliser

Lire le Guide_consultation_experts_FR.pdf et imprimer la fiche individuelle. Les formulaires reponses_experts.csv et observations_trajets.csv sont vides. Aucun poids d'expert ni observation n'a été produit.

Après des entretiens réels, saisir les allocations totalisant 100 et exécuter, depuis ce dossier sous CMD ou PowerShell:

```
py -m pip install numpy pandas
py analyser_consultation.py
```

Sans réponses le script conserve un statut en attente. Les résultats du dossier comparaison_CRITIC sont calculés sur la dispersion et les corrélations des scores, pas sur des avis d'experts. Les montrer seulement après les réponses indépendantes pour limiter l'ancrage. Une opinion ne remplace pas une observation d'accès ou un trajet mesuré. Les identifiants personnels et consentements restent hors du dépôt public.
