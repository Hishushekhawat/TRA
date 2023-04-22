


def authenticate(request):
    try:
        request.session["user_token"]
        return True
    except Exception as e:
        return False
