from django_cas_ng import views
from django.http import HttpResponseRedirect,JsonResponse
from wechat.session import add_session

def cas_check(request):
        if(request.user.isauthenticate()):
            #get username
            username=request.user.get_username()
            #set identity to student
            identity='student'
            #add session
            add_session(request, identity=identity, username=username)
            return JsonResponse({
                'status': 'ok',
                'identity': identity,
            })
    else:
        return JsonResponse({
                'status': 'error',
                'identity': 'none',
            })
