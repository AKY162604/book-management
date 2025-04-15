from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain, hashed):
    """
    Verify if a plain text password matches its hashed version.

    Args:
        plain (str): The plain text password to verify.
        hashed (str): The hashed password to compare against.

    Returns:
        bool: True if the plain text password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain, hashed)

def hash_password(password):
    """
    Hashes a given password using a secure hashing algorithm.

    Args:
        password (str): The plain text password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)