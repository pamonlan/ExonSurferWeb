from django.shortcuts import render

#Index view
def index(request):
    """
    Index view
    """
    return render(request, 'index.html')
