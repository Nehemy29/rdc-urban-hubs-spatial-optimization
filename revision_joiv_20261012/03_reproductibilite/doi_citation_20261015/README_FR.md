# Citation confirmée de l’archive v2.0.0

Le DOI 10.5281/zenodo.23389655 désigne v2.0.0, publiée le 15 octobre 2026 à partir du commit 8a4a186. Le DOI 10.5281/zenodo.22287395 désigne v1.0.0 et le DOI 10.5281/zenodo.22287394 regroupe toutes les versions.

Les documents actuels de soumission ajoutent la citation après publication. Ils n’ont pas été réinjectés dans l’archive immuable v2.0.0. Le code, les données et les calculs de cette archive sont inchangés; son texte antérieur indiquant que le DOI restait à ajouter est historique.

Après les éventuelles reconstructions des modules précédents, exécuter depuis 03_reproductibilite :

```
py -m pip install python-docx
py doi_citation_20261015/update_documents.py
```

Le sous-dossier deliverables de ce module contient les trois documents Word avec la citation finale. Les entrées conservées sont les documents du 12 octobre. Le script ne recalcule aucun résultat et ne modifie aucun tableau ou figure. Les versions prêtes à soumettre sont aussi dans 01_manuscrit, 02_reponse et completion/final. Les PDF livrés ont été rendus et contrôlés après l’amendement.
