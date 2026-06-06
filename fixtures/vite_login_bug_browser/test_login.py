from login import login_token

assert login_token({"token": "abc"}) == "abc", "login_token must return the user's token"
print("login tests passed")
