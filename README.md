# Weather Message Rules

*"Ajoute les règles métier et les données suivantes à l'application de décompte des messages météo :

1. Liste des Agents (Menu déroulant obligatoire lors de la saisie) :

DALO CLEMENT

DAO LEA

OTE ARMANDE

KOFFI GISELE

ADOH BOUET

DJAGBA BIENVENU

2. Types de messages (Menu déroulant) avec gestion des heures théoriques :

METAR (valide uniquement pour les heures de 07h à 20h)

METREPORT (valide uniquement pour les heures de 07h à 20h)

SPECI (valide pour toutes les heures, déclenché à la demande)

SYNOP Horaire (valide pour toutes les heures)

SYNOP Principal (valide uniquement pour les heures tri-horaires : 00h, 03h, 06h, 09h, 12h, 15h, 18h, 21h)
Note : Si l'utilisateur choisit une heure non valide pour le type de message, affiche une alerte visuelle.

3. Règle stricte du délai de transmission (H+5) :

L'heure limite de transmission est calculée automatiquement : c'est l'heure du message + 5 minutes (Exemple : pour le message de 13h00, l'heure limite est 13h05).

Lorsque l'agent clique sur 'Transmettre', l'application compare l'heure réelle de clic avec cette heure limite (H+5). Si l'heure réelle est inférieure ou égale, le message est marqué 'Dans le délai'. Si elle dépasse, il est 'Hors délai'.

4. Évolutions de l'interface :

Dans le tableau récapitulatif, ajoute une colonne 'Agent' et une colonne 'Type de message'.

Ajoute un filtre en haut de la page pour pouvoir filtrer les statistiques et le tableau par Agent."*

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://aero-log-keeper.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/17228e50-e356-40b9-9b82-c9165bc3eeb5).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
