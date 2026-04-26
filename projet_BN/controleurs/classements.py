from model.model_pg import get_classement

classement = get_classement(SESSION['CONNEXION'])
REQUEST_VARS['classement'] = classement
