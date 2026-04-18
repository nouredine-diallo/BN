from model.model_pg import chercher_joueur, ajouter_joueur_humain


if POST and 'btn_chercher' in POST:
    pseudo = POST['pseudo_recherche'][0]
    
    if len(pseudo.strip()) > 0:
        resultats = chercher_joueur(SESSION['CONNEXION'], pseudo)
        
        if resultats:
            REQUEST_VARS['resultats_recherche'] = resultats
            REQUEST_VARS['message'] = f"{len(resultats)} joueur(s) trouvé(s) pour '{pseudo}'."
            REQUEST_VARS['message_class'] = "alert-success"
        else:
            REQUEST_VARS['message'] = f"Aucun résultat pour '{pseudo}'."
            REQUEST_VARS['message_class'] = "alert-warning"
            
    else:
        REQUEST_VARS['message'] = "Veuillez taper un pseudo avant de chercher."
        REQUEST_VARS['message_class'] = "alert-error"


elif POST and 'btn_choisir' in POST:
   
    id_choisi = int(POST['id_joueur_choisi'][0])
    
    
    SESSION['id_joueur'] = id_choisi
    
    REQUEST_VARS['redirection'] = "/"

elif POST and 'btn_inscrire' in POST:
    pseudo_insc = POST['pseudo_insc'][0]
    nom_insc = POST['nom_insc'][0]
    prenom_insc = POST['prenom_insc'][0]
    date_naiss_insc = POST['date_naiss_insc'][0]
    
    if len(pseudo_insc.strip()) > 0 and len(nom_insc.strip()) > 0:
        #on ajoute la date de creation apres 
        nouvel_id = ajouter_joueur_humain(SESSION['CONNEXION'], pseudo_insc, nom_insc, prenom_insc, date_naiss_insc)
        
        if nouvel_id:
            # SUCCÈS 
            SESSION['id_joueur'] = nouvel_id
            REQUEST_VARS['redirection'] = "/"
        else:
            REQUEST_VARS['message'] = "Erreur lors de l'inscription (Pseudo déjà pris ?)."
            REQUEST_VARS['message_class'] = "alert-error"
    else:
        REQUEST_VARS['message'] = "Veuillez remplir tous les champs."
        REQUEST_VARS['message_class'] = "alert-error"