class Config:
    SECRET_KEY = "supersecretkey"
    SQLALCHEMY_DATABASE_URI = "sqlite:///peer_eval.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin info
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"

    # Starting coins for users
    STARTER_COIN = 10
