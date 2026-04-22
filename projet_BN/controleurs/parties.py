from model.model_pg import get_parties_en_cours, get_parties_terminees, get_jv, ajouter_joueur_virtuel, creer_partie, creer_pioche


if 'id_joueur' not in SESSION:
    SESSION['id_joueur'] = 1

id_joueur_courant = SESSION['id_joueur']



#  Créer un nouveau Joueur Virtuel 
if POST and 'creer_jv' in POST: 
    pseudo_jv = POST['pseudo_jv'][0]
    niveau_jv = POST['niveau_jv'][0]

    new_id = ajouter_joueur_virtuel(SESSION['CONNEXION'], pseudo_jv, niveau_jv, id_joueur_courant)

    if new_id: 
        REQUEST_VARS['message'] = f"Le joueur virtuel '{pseudo_jv}' a été créé avec succès."
        REQUEST_VARS['message_class'] = "alert-success"
    else:
        REQUEST_VARS['message'] = "Erreur lors de la création du joueur virtuel (Pseudo existant ?)."
        REQUEST_VARS['message_class'] = "alert-error"

# Lancer une Nouvelle Partie
elif POST and 'nouvelle_partie' in POST: 
    id_adv = POST['id_adversaire'][0]
    
    
    id_nouvelle_partie = creer_partie(SESSION['CONNEXION'], id_joueur_courant, id_adv) 
        
    if id_nouvelle_partie:
        # Création de la pioche liée à la partie
        id_pioche = creer_pioche(SESSION['CONNEXION'], id_nouvelle_partie, "Distrib 1")
        
        if id_pioche:
            # Redirection  plateau de jeu
            REQUEST_VARS['redirection'] = f"/jeu?id={id_nouvelle_partie}"
        else:
            REQUEST_VARS['message'] = "Erreur : La partie a été créée, mais la pioche a échoué."
            REQUEST_VARS['message_class'] = "alert-error"
    else:
        REQUEST_VARS['message'] = "Erreur lors de la création de la nouvelle partie."
        REQUEST_VARS['message_class'] = "alert-error"




# On récupère les données 
parties_en_cours = get_parties_en_cours(SESSION['CONNEXION'], id_joueur_courant)
parties_terminees = get_parties_terminees(SESSION['CONNEXION'], id_joueur_courant)
liste_jv = get_jv(SESSION['CONNEXION'])

# On les envoie au template 
REQUEST_VARS['parties_en_cours'] = parties_en_cours
REQUEST_VARS['parties_terminees'] = parties_terminees
REQUEST_VARS['liste_jv'] = liste_jv