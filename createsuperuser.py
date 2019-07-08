from models import Users
from app import db
from validate_email import validate_email


print("Enter login")
login = input()
print("Enter email")
email = input()
print("Enter password")
password = input()
print("Confirm password")
password_two = input()
is_valid = validate_email(email)
if password == password_two and is_valid:
    user = Users(login=login, email=email, root=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
else:
    print("wrong data")