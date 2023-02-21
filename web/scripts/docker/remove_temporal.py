from primerblast.model import Session

#Get all user from the database and remove temporal
for session in Session.objects.all():
    try:
        session.remove_temporal()
    except:
        pass