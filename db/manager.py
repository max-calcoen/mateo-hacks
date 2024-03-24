from .account import Account
from .request import Request
import sqlite3
import bcrypt


class Manager:
    __db_str = ""

    def __init__(self, db_str):
        self.__db_str = db_str

    def get_account(self, email):
        con = sqlite3.connect(self.__db_str)
        cur = con.cursor()
        cur.execute("SELECT * FROM accounts WHERE email = ?", (email,))
        account = cur.fetchone()
        con.close()
        if account is not None:
            return self.__account_creation_helper(account)
        else:
            return None

    def add_account(self, fname, lname, email, pw, type) -> Account:
        con = sqlite3.connect(self.__db_str)
        cur = con.cursor()
        pw = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())
        try:
            cur.execute(
                "INSERT INTO accounts (fname, lname, email, pw, type) VALUES (?, ?, ?, ?, ?);",
                (
                    fname,
                    lname,
                    email,
                    pw,
                    type,
                ),
            )
            id = cur.lastrowid

            con.commit()
            cur.close()
            return Account(id, fname, lname, email, pw, type)
        except:
            return None

    def get_all_requests(self):
        con = sqlite3.connect(self.__db_str)
        cur = con.cursor()
        cur.execute("SELECT * FROM requests")
        requests = cur.fetchall()
        con.close()

        print(requests)

        return [self.__request_creation_helper(request) for request in requests]

    def get_attorney_requests(self, attorney):
        con = sqlite3.connect(self.__db_str)
        cur = con.cursor()
        cur.execute("SELECT * FROM requests WHERE attorney_id=?;", (str(attorney.id),))
        req = cur.fetchall()
        con.close()
        return req

    def add_request(self, request: Request):
        con = sqlite3.connect(self.__db_str)
        cur = con.cursor()
        try:
            with con:
                cur.execute(
                    "INSERT INTO requests (attorney_id, ISBN, prison_title) VALUES (?, ?, ?);",
                    (request.attorney_id, request.isbn, request.prison_title),
                )
                con.commit()
                cur.close()
                return True
        except:
            cur.close()
            return False

    def remove_request(self, request_id):
        con = sqlite3.connect(self.__db_str)
        cur = con.cursor()
        try:
            cur.execute(f'DELETE FROM requests WHERE rowid = "{request_id}"')
            con.commit()
            cur.close()
            return True
        except:
            return False

    def __account_creation_helper(self, db_string):
        return Account(
            db_string[0],
            db_string[1],
            db_string[2],
            db_string[3],
            db_string[4],
            db_string[5],
        )

    def __request_creation_helper(self, db_string):
        return Request(
            db_string[0], db_string[1], db_string[2], db_string[3], db_string[4]
        )
