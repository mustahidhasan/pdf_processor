# utils.py
import jwt
import datetime
from settings import SECRET_KEY


def generate_jwt(user_email, user_id):
    """
    Generates a JWT token with user details.

    :param user_email: The email of the user
    :param user_id: The ID of the user
    :return: JWT token
    """
    iat = datetime.datetime.utcnow()  # Issued at time
    exp = iat + datetime.timedelta(days=1)  # Token expires in 1 hour
    payload = {
        "sub": user_email,
        "iss": "comax",
        "aud": "Splitter",
        "user_id": user_id,
        "iat": iat.timestamp(),
        "exp": exp.timestamp(),
    }

    # Sign and encode the JWT with the secret key
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    print("token", token)
    return token


if __name__ == "__main__":
    generate_jwt("admin@gmail.com", "admin")
