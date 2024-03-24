import sqlite3
from os import getenv


if __name__ == "__main__":
    con = sqlite3.connect(getenv("DATABASE_PATH"))

    with open("db/reset_db.sql") as f:
        con.executescript(f.read())
    con.commit()
    con.close()
