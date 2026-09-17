# Fly-in - Guide

Ce document retrace, étape par étape, comment ce projet **Fly-in** a été conçu et construit : les choix, les blocages rencontrés, les erreurs faites (et pourquoi elles arrivaient), et comment elles ont été corrigées. L'objectif est de pouvoir s'en servir comme support pour enseigner le projet à quelqu'un d'autre, en montrant non seulement le résultat final mais **le raisonnement derrière chaque décision**.

---

## 1. Comprendre le sujet avant de coder

Avant d'écrire la moindre ligne de code, il faut extraire du sujet les **contraintes non négociables** :

- Écrire en Python 3.10+, avec **typage strict** (`mypy`) et respect de `flake8`.
- **Aucune bibliothèque de graphe** (`networkx`, `graphlib`, etc. interdits) - le graphe doit être implémenté à la main.
- Le projet doit être **complètement orienté objet**.
- Le format d'entrée est un fichier texte custom (`nb_drones:`, `start_hub:`, `end_hub:`, `hub:`, `connection:`), avec des métadonnées optionnelles entre crochets.
- Quatre types de zones : `normal` (1 tour), `restricted` (2 tours), `priority` (1 tour, à privilégier), `blocked` (infranchissable).
- Des contraintes de capacité : `max_drones` par zone, `max_link_capacity` par connexion.
- Les drones peuvent bouger **simultanément**, mais doivent respecter les capacités et ne pas entrer en collision.
- Le format de sortie est strict : une ligne par tour, `D<ID>-<zone>` ou `D<ID>-<connexion>` (pour les zones restricted en transit), drones immobiles omis.
- Une **représentation visuelle** est obligatoire (terminal coloré et/ou GUI).

**Leçon** : lire tout le sujet *avant* de coder évite de repartir de zéro plus tard. Beaucoup de contraintes du sujet (comme le coût de 2 tours pour `restricted`, ou le fait qu'une connexion "s'occupe" pendant le transit) ont des implications profondes sur l'architecture - les rater au début coûte cher après.

---

## 2. Choix d'architecture initial

Le projet a été structuré ainsi :

```
src/
├── main.py
├── parser.py
├── algorithms.py       (ReservationTable, PathFinder, RoutingManager)
├── simulate.py          (SimulationEngine)
├── visualizer.py         (GUI Arcade)
└── models/
    ├── zone.py
    ├── connection.py
    ├── drone.py
    └── network.py
```

Chaque classe a une responsabilité unique - c'est un principe central pour respecter la contrainte "complètement orienté objet" du sujet, et ça se voit très bien dans le découpage : le parsing, le modèle de données, l'algorithme de recherche de chemin, l'ordonnancement des drones, la génération de la sortie texte et la visualisation sont **cinq responsabilités distinctes**, dans cinq endroits distincts.

---

## 3. Le premier blocage : les imports incohérents

**Ce qui s'est passé** : dès le début, certains fichiers importaient `from models.zone import Zone` (sans préfixe), d'autres `from src.models.zone import Zone` (avec préfixe). Ça semblait fonctionner... jusqu'à ce que `mypy` explose avec :

```
error: Source file found twice under different module names: "models.zone" and "src.models.zone"
```

**Pourquoi ça arrive** : pour Python (et mypy), `models.zone` et `src.models.zone` sont **deux noms de module différents**, même s'ils pointent vers le même fichier physique sur le disque. Si la moitié du projet importe d'une façon et l'autre moitié de l'autre, l'outil de typage voit "deux classes `Zone` différentes" qui devraient être la même.

**La leçon à enseigner ici** : ce genre d'erreur est très courant chez les débutants qui changent leur structure de dossiers en cours de route sans être rigoureux sur la convention d'import. **Il faut choisir UNE convention (avec ou sans le préfixe du package racine) et s'y tenir partout**, y compris dans `main.py`.

Un point technique lié : la présence ou l'absence de `__init__.py` dans chaque dossier (`src/`, `src/models/`) change comment Python et mypy résolvent les imports. Avoir un `__init__.py` dans `src/models/` mais pas dans `src/` créait justement cette ambiguïté.

---

## 4. Construire le Parser : ligne par ligne, avec rigueur

Le `Parser` a été construit progressivement :

1. **D'abord, juste `nb_drones:`** - la structure de base (`ParseError` avec numéro de ligne, `_reset()` pour réutiliser l'instance, une méthode `_parse_line` qui route chaque ligne selon son préfixe).
2. **Ensuite, les zones** (`hub:`, `start_hub:`, `end_hub:`) avec parsing des métadonnées entre crochets.
3. **Enfin, les connexions**, avec détection de doublons (une connexion `A-B` et `B-A` doivent être considérées comme la même) et vérification que les deux zones référencées existent déjà.

**Décision de conception importante** : le parser fait **une seule passe** sur le fichier. Ça implique une contrainte réelle - une connexion ne peut référencer que des zones **déjà vues avant elle** dans le fichier. Ce n'est pas une limitation arbitraire : le sujet le dit explicitement ("*Connections must link only previously defined zones*"), donc l'implémentation colle exactement à l'exigence, sans complexité inutile (pas besoin de "résolution en deux passes").

**Un vrai bug rencontré** : à un moment, le parser retournait un objet `Network()` totalement vide, car les attributs `self.zones`, `self.start_zone`, etc., n'étaient déclarés qu'en **annotation de type**, sans valeur initiale :
```python
self.zones: list[Zone]   # ← déclare le type, mais n'assigne RIEN
```
Ça compile, mais l'attribut n'existe pas tant que quelque chose ne l'assigne pas explicitement. La correction :
```python
self.zones: list[Zone] = []
```

**Leçon** : en Python, une annotation de type seule (`x: int`) ne crée PAS de variable - il faut toujours l'accompagner d'une valeur (`x: int = 0`) si on veut qu'elle existe réellement à l'exécution.

---

## 5. Concevoir l'algorithme : rejeter la sur-ingénierie

Avant de coder l'algorithme de routage, une IA (Gemini) avait proposé une architecture "Stratégie hybride" combinant Max-Flow (Edmonds-Karp), A\* spatiotemporel, et BFS de validation - trois algorithmes différents selon le "type" de graphe détecté.

**Pourquoi cette proposition a été rejetée** :
1. Le Max-Flow maximise un débit, mais ne donne **pas** un ordonnancement temporel (qui bouge à quel tour) - il aurait fallu reconvertir le flot en planning après coup, doublant le travail.
2. Détecter dynamiquement "quel type de graphe" ajoute de la complexité fragile, sans garantie que le sujet fournisse des graphes qui rentrent proprement dans ces catégories.
3. Trois algorithmes différents, c'est trois fois plus de code à maintenir, tester, et expliquer en soutenance.

**La décision retenue : Cooperative A\***("Hierarchical Cooperative A*", HCA*) - un seul algorithme, plus simple :
- Chaque drone est routé **un par un**, dans un ordre donné.
- Chaque drone calcule son chemin optimal via une recherche de plus court chemin sur un **état temps-étendu** : pas juste `zone`, mais `(zone, tour)`.
- Une fois le chemin trouvé, il est **réservé** dans une structure partagée (`ReservationTable`), pour que les drones suivants en tiennent compte.

**Leçon** : quand une IA (ou n'importe qui) propose une solution complexe, il faut se demander "est-ce que ça résout vraiment le problème plus simplement, ou est-ce que ça déplace juste la complexité ailleurs ?". Ici, le Cooperative A\* atteint les mêmes objectifs (distribution sur chemins multiples, attente stratégique, évitement de conflits, contraintes de capacité) avec une seule structure de données et un seul algorithme.

---

## 6. La ReservationTable : la brique centrale

### Conception

La `ReservationTable` garde en mémoire, pour chaque tour futur :
- combien de drones occupent chaque **zone** à ce tour (`{(zone_name, turn): count}`)
- combien de drones traversent chaque **connexion** à ce tour (`{(canonical_edge, turn): count}`)

Deux méthodes de lecture (`is_zone_available`, `is_connection_available`) et deux méthodes d'écriture (`reserve_zone`, `reserve_connection`), plus une méthode de haut niveau (`reserve_path`) qui pose toutes les réservations d'un chemin complet en une fois.

### Le piège des zones "restricted" - et l'erreur corrigée

On m'avait suggéré que, pour un transit de 2 tours vers une zone `restricted`, il fallait réserver :
- la connexion au tour `t`
- **la zone destination** aux tours `t+1` **ET** `t+2`

**Pourquoi c'était faux** : le sujet dit explicitement que le drone **occupe la connexion** pendant les 2 tours de transit - il n'est physiquement dans la zone destination **qu'au tour d'arrivée** (`t+2`), pas avant. Réserver la zone dès `t+1` aurait bloqué inutilement sa capacité un tour trop tôt, empêchant potentiellement un autre drone d'y entrer légitimement à ce moment-là alors que la zone était en réalité encore libre.

**La correction appliquée** :
- Connexion réservée aux tours `t` et `t+1` (les 2 tours de transit)
- Zone destination réservée **seulement** à `t+2`

**Leçon** : les suggestions doivent être vérifiées contre le texte exact du sujet. Ici, relire attentivement la phrase *"the drone occupies the connection during transit"* a suffi à repérer l'erreur - le sujet parle de la connexion, pas de la zone, pendant le transit.

### Exception start/end

Le sujet précise que `start_hub` et `end_hub` n'ont **pas** de limite de capacité (tous les drones peuvent y coexister). Ça s'est traduit par deux attributs `is_start`/`is_end` sur `Zone`, court-circuitant la vérification de capacité dans `is_zone_available` :
```python
def is_zone_available(self, zone: Zone, turn: int) -> bool:
    if zone.is_start or zone.is_end:
        return True
    ...
```

**Petite remarque** : ces attributs `is_start`/`is_end` ont été ajoutés à `Zone` *après coup*, une fois que j'ai réalisé pendant la conception de `ReservationTable` que j'en avais besoin. Le `Parser` a dû être modifié après-coup pour les positionner (`zone.is_start = True` au moment de créer la zone `start_hub`). **Ça illustre bien que la conception d'un projet n'est jamais parfaitement linéaire** - des besoins émergent au fur et à mesure qu'on avance dans les détails d'implémentation, même avec un bon design de départ.

---

## 7. Le PathFinder : Dijkstra sur un état temps-étendu

### Pourquoi Dijkstra et pas A\*

Un vrai A\* aurait besoin d'une heuristique admissible (par exemple, distance à vol d'oiseau divisée par le coût minimal de déplacement). Vu la taille des cartes du sujet (au plus 25 drones, quelques dizaines de zones), un Dijkstra simple est largement suffisant en performance, et évite d'avoir à concevoir/justifier une heuristique. **Décision pragmatique** : ne pas sur-optimiser une partie du système qui n'en a pas besoin.

### L'état exploré

Chaque nœud du Dijkstra n'est pas juste "une zone", mais **une paire `(zone, tour)`**. Ça permet de représenter le fait qu'une même zone peut être libre à un tour donné et occupée à un autre.

### Un bug classique : dépiler avant la boucle

Voici un bug réel rencontré : la queue de priorité était vidée d'un seul élément juste après y avoir été remplie, **avant même d'entrer dans la boucle `while`** :
```python
heapq.heappush(priority_queue, (0, start_zone.name, start_turn))
cost, zone_name, turn = heapq.heappop(priority_queue)   # <-- bug : dépile trop tôt

while priority_queue:   # <-- la queue est déjà vide ici !
    ...
```
Résultat : la boucle ne s'exécutait jamais, et l'algorithme retournait toujours "aucun chemin trouvé", même pour des cartes simples. Un simple `print` de debug (`len(best_cost)`) a révélé qu'un seul état avait été exploré - signe évident que la boucle ne tournait pas.

**Leçon** : quand un algorithme "ne trouve jamais de solution" même sur un cas trivial, la première chose à vérifier, ce n'est pas la logique de l'algorithme lui-même, mais **si la boucle principale s'exécute réellement**. Un simple print de la taille des structures explorées suffit souvent à localiser le problème en 30 secondes.

### Comparabilité des tuples dans heapq

Autre piège technique : `heapq` compare les tuples élément par élément. Si deux entrées ont le même coût, Python tente de comparer l'élément suivant - s'il s'agit d'un objet `Zone`, ça plante (pas d'ordre défini sur `Zone`). **Solution** : stocker le **nom** de la zone (une chaîne, comparable) dans la queue plutôt que l'objet lui-même, et retrouver l'objet réel via un dictionnaire `{nom: Zone}` construit une fois dans `__init__`.

**Leçon** : c'est un piège très courant avec `heapq` en Python - toujours réfléchir à ce qui se passe en cas d'égalité de coût, et s'assurer que tous les éléments du tuple sont naturellement comparables (ou ajouter un compteur/tie-breaker).

---

## 8. Le RoutingManager : orchestrer plusieurs drones

Une fois `find_path` fiable pour un seul drone, il fallait router **tous** les drones, dans un ordre donné, en tenant compte des réservations précédentes.

### La question de l'ordre

Une réflexion a été menée sur "dans quel ordre router les drones pour minimiser le temps total ?" - plusieurs stratégies ont été envisagées (tri par distance décroissante, essais multiples, heuristiques diverses).

**Découverte importante** : comme le sujet garantit **un seul** `start_hub` et **un seul** `end_hub`, partagés par tous les drones, **l'ordre de passage n'a strictement aucun effet** sur le résultat global - les drones sont interchangeables. Une stratégie de tri par "distance au but" proposée initialement était donc **inutile**, puisque cette distance est identique pour tous.

**Analyse du "problème" observé** : sur une carte de test, le dernier drone routé mettait beaucoup plus de tours que les autres. Ça ressemblait à un défaut de l'algorithme ("glouton, pas de replanification globale"). Mais un calcul manuel de la limite théorique (basé sur le débit des deux routes parallèles disponibles) a montré que **le résultat obtenu était déjà l'optimum théorique** compte tenu des contraintes de capacité du réseau - ce n'était pas un bug, ni une inefficacité corrigible, juste la réalité physique du goulot d'étranglement de la carte.

**Leçon** : avant d'investir du temps à "optimiser" un algorithme parce qu'un résultat "semble" mauvais, il faut d'abord vérifier s'il existe réellement une meilleure solution - parfois, ce qui ressemble à un défaut est en fait la limite physique du problème.

### Gestion de l'échec

Si `find_path` ne trouve aucun chemin pour un drone (carte impossible, deadlock structurel), une exception dédiée `RoutingError` est levée, avec le nom du drone concerné - plutôt que de continuer silencieusement avec un état incohérent.

---

## 9. Le SimulationEngine : transformer les chemins en sortie texte

Cette classe convertit les `routes` (chemins calculés par drone) en lignes de sortie conformes au format exact du sujet.

### Règle de conversion

Pour chaque paire consécutive `(zone_actuelle, tour) → (zone_suivante, tour_suivant)` d'un chemin :
- **Attente** (même zone) → omis de la sortie
- **Mouvement normal/priority** (+1 tour) → une seule action `D<ID>-<zone>`
- **Transit restricted** (+2 tours) → **deux actions séparées à deux tours différents** : `D<ID>-<connexion>` au premier tour du transit, puis `D<ID>-<zone>` à l'arrivée

### Deux bugs "off-by-one" classiques rencontrés

1. **`range(len(timed_path) - 2)`** au lieu de `- 1` - cette erreur faisait **rater systématiquement la toute dernière transition** de chaque chemin (le dernier mouvement de chaque drone n'était jamais affiché).
2. **`range(1, max_turn)`** au lieu de `range(1, max_turn + 1)` - la borne supérieure de `range` étant exclusive en Python, ça faisait **rater le dernier tour** de la simulation (celui où le dernier drone arrive).

**Leçon** : les erreurs "off-by-one" (décalage d'un cran) sont extrêmement fréquentes avec les boucles et les indices en Python. Le réflexe à avoir : pour parcourir toutes les paires consécutives d'une liste de longueur N, c'est toujours `range(N - 1)`. Pour inclure une borne supérieure dans un `range`, il faut toujours lui ajouter `+ 1`.


---

## 10. La partie visuelle : Arcade

### Pourquoi Arcade plutôt que pygame (l'idée de depart)

Arcade offre une API plus moderne (sprites, animations, gestion d'événements structurée via `on_draw`/`on_update`/`on_key_press`) pour un effort de portage raisonnable - un bon compromis "qualité visuelle vs complexité d'implémentation" pour ce projet.

### Construction progressive

1. **D'abord, une version minimale** : zones en cercles colorés, drones en cercles, une ligne par connexion, lecture automatique tour par tour.
2. **Puis, des sprites réels** : un fond d'écran, une feuille de sprites pour les drones (découpée en frames pour l'animation), des textures dédiées par type de zone.
3. **Puis, des contrôles interactifs** : pause/lecture, avance/recul manuel au clavier, glisser-déposer (pan) à la souris, zoom à la molette centré sur le curseur.
4. **Enfin, un HUD compact** de style "tech/space" plutôt qu'un simple texte brut.

### Le bug d'interpolation le plus intéressant à expliquer

Au début, la position d'un drone à l'écran était calculée en comparant le tour courant à `floor(tour)` et `floor(tour) + 1` - ce qui fonctionne pour un mouvement d'1 tour, mais **casse complètement** pour un transit `restricted` de 2 tours : le drone semblait "faire une pause" au milieu du transit avant de "sauter" à l'arrivée, un comportement visuel incohérent.

**La correction** : au lieu de comparer à des intervalles fixes d'1 tour, il fallait retrouver directement, dans le chemin complet du drone, le **segment réel** contenant le tour courant - segment qui peut durer 1 tour (mouvement normal), 2 tours (transit restricted), ou 0 tour (attente) - puis interpoler proportionnellement à l'intérieur de ce segment, quelle que soit sa durée réelle.

**Leçon** : une animation "par tour fixe" est une simplification qui ne tient pas quand les événements du domaine métier (ici, les tours de transit) n'ont pas tous la même durée. Il faut faire correspondre la granularité de l'animation à la granularité réelle des événements, pas à une unité de temps arbitraire.

### Un problème de bibliothèque tierce mal typée

`mypy --strict` refusait de compiler `class Visualizer(arcade.Window)`, car la bibliothèque Arcade elle-même n'expose pas de types complets pour certaines de ses classes (elles apparaissent comme `Any`). Solution : un commentaire ciblé `# type: ignore[misc]` sur cette ligne précise, et une entrée dans `pyproject.toml` pour désactiver ce code d'erreur spécifiquement sur le module `visualizer` :
```toml
[[tool.mypy.overrides]]
module = "visualizer"
disable_error_code = ["attr-defined", "misc"]
```

**Leçon** : quand un outil de vérification statique donne des résultats qui semblent changer "sans raison" entre deux runs identiques, le cache est souvent le coupable - c'est un réflexe de debug à avoir pour tous les outils qui en utilisent un (mypy, mais aussi des compilateurs, des bundlers, etc.).

---

## 11. Robustesse et gestion d'erreurs
 
Le sujet insiste sur le fait qu'un programme robuste **ne doit jamais crasher brutalement** face à une entrée invalide - toute erreur doit être gérée proprement, avec un message clair plutôt qu'une trace Python brute.
 
### Les couches de protection mises en place
 
1. **Erreurs de parsing** (`OSError`, `ParseError`, `ValueError`) - attrapées explicitement dans `main()`, message clair sur `stderr`, sortie propre avec `sys.exit(1)`.
2. **Erreurs de routage** (`RoutingError`)
3. **Filet de sécurité générique** - un dernier `except Exception` englobant, pour capturer tout ce qui n'a pas été anticipé (y compris une éventuelle erreur d'initialisation de la bibliothèque graphique en environnement sans affichage).

**Leçon** : la gestion d'erreurs n'est pas une réflexion "après coup" idéale, mais dans ce projet précis, elle a quand même été largement traitée en fin de parcours, une fois le cœur fonctionnel stabilisé. C'est un compromis raisonnable : d'abord faire fonctionner la logique, ensuite la blinder - tant que le blindage n'est pas oublié avant le rendu final.
 
---
 
## 12. Répondre aux questions de réflexion du sujet
 
Le sujet pose explicitement une série de questions pour t'aider à évaluer ton propre algorithme. Voici des réponses basées sur l'implémentation réelle.
 
### Quelle est l'efficacité de l'algorithme ?
 
Le cœur de l'algorithme est un Dijkstra classique, exécuté une fois par drone, sur un espace d'états `(zone, tour)` plutôt que juste `zone`. Chaque vérification de disponibilité (`is_zone_available`, `is_connection_available`) est un simple accès dictionnaire, donc en `O(1)` amorti. L'algorithme reste donc aussi efficace qu'un Dijkstra standard, juste sur un graphe un peu plus grand (le produit "zones × tours" plutôt que juste "zones").
 
### Peut-il fonctionner avec un grand nombre de drones ?
 
Oui - testé avec 25 drones sur une carte complexe (une trentaine de zones, plusieurs embranchements, un mini-labyrinthe, des zones `restricted`/`priority`/`blocked`), sans problème de performance ni de blocage. Le seul facteur limitant est la borne de sécurité sur le nombre de tours explorés (`Z * 4`, où `Z` est le nombre de zones), qui garantit que la recherche se termine toujours, y compris quand aucun chemin n'existe.
 
### Quelle est la complexité ?
 
Pour un seul drone : `O((Z * T) * log(Z * T))`, où `Z` est le nombre de zones et `T` la borne de tours explorée (proportionnelle à `Z`) - c'est la complexité standard d'un Dijkstra (`O(E log V)`) appliqué à un graphe d'états de taille `Z * T`. Pour router tous les drones : cette recherche est répétée `D` fois (une par drone), donnée séquentiellement, donc `O(D * Z * T * log(Z * T))` au total. Les vérifications de capacité (`ReservationTable`) restent en `O(1)` amorti à chaque étape, donc elles n'aggravent pas cette complexité.
 
### Recalcule-t-on les chemins, ou sont-ils mis en cache ?
 
Chaque drone calcule son chemin **une seule fois** (`find_path`), puis ce chemin est stocké tel quel dans le dictionnaire `routes` retourné par `RoutingManager.route_all_drones`. Il n'y a **aucun recalcul** : une fois qu'un drone a un chemin, il le garde jusqu'à la fin - ni `SimulationEngine` ni `Visualizer` ne relancent de recherche, ils se contentent de lire les chemins déjà calculés et de les rejouer/interpoler dans le temps.
 
### Quel est l'impact sur la mémoire ?
 
Trois structures dominent l'usage mémoire :
- La `ReservationTable` : deux dictionnaires qui grandissent proportionnellement au nombre de réservations posées, donc au pire `O(D * longueur moyenne des chemins)` entrées au total - reste petit même avec beaucoup de drones, puisque chaque drone ne réserve que les créneaux de son propre chemin.
- Les structures temporaires de chaque recherche (`best_cost`, `predecessor`, la file de priorité) : elles ne vivent que le temps d'un appel à `find_path`, puis sont libérées (portée locale à la méthode) - elles ne s'accumulent pas entre drones.
- Les `routes` finales : une liste de `(zone, tour)` par drone, donc proportionnelle au nombre de drones multiplié par la longueur de leurs chemins respectifs - reste très raisonnable même pour 25 drones sur une grande carte.
### Comment la représentation visuelle enrichit-elle la compréhension de la simulation ?
 
Voir la partie 10 pour le détail des fonctionnalités. En résumé : la sortie texte donne l'information brute (qui bouge où, à quel tour), mais ne montre pas *visuellement* la congestion, les détours, ou la façon dont les drones se répartissent sur des chemins parallèles. La visualisation Arcade rend ça immédiat à l'œil - on voit en un coup d'œil un embouteillage sur une zone `restricted` à faible capacité, ou une répartition équilibrée entre deux routes concurrentes, ce qui serait beaucoup plus long à repérer en lisant seulement des lignes de texte.
 
### L'algorithme atteint-il les objectifs de performance visés ?
 
Sur les cartes testées, oui, largement. Par exemple, une carte "hard" avec 8 drones et un mini-labyrinthe a été résolue en 14 tours. Une carte plus simple à 5 drones avec deux routes parallèles (dont une via une zone `restricted`) a été résolue en 6 tours - un calcul manuel de la limite théorique du réseau a confirmé que ce résultat était déjà l'optimum possible compte tenu des contraintes de capacité, pas seulement "une bonne solution".
 
### Quelles optimisations ont été mises en place ?
 
Volontairement peu, par choix de conception : le Dijkstra de base, couplé à des vérifications de capacité en `O(1)`, s'est avéré suffisant pour rester largement sous les seuils de tours visés sans optimisation supplémentaire. Plutôt que d'ajouter de la complexité algorithmique (une heuristique A\*, une réoptimisation de l'ordre de routage, etc.) sans preuve qu'elle était nécessaire, la priorité a été mise sur la correction et la robustesse de l'algorithme de base. Une piste d'optimisation aurait été de trier ou réordonner les drones pour réduire le temps total - mais comme expliqué en partie 8, ça n'aurait eu aucun effet ici, puisque le réseau n'a qu'un seul point de départ et d'arrivée partagé par tous les drones.
 
---
