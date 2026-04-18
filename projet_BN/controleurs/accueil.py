from model.model_pg import get_stat_joueur , get_pseudo_joueur
if 'id_joueur' not in SESSION:
    SESSION['id_joueur'] = 1
id_joueur_connect= SESSION['id_joueur']
stats= get_stat_joueur(SESSION['CONNEXION'] , id_joueur_connect)
pseudo = get_pseudo_joueur(SESSION['CONNEXION'], id_joueur_connect)

REQUEST_VARS['statistiques']=stats
REQUEST_VARS['pseudo_joueur'] = pseudo 