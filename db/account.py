import bcrypt
import json


class Account:
    def __init__(self, id, fname, lname, email, pw, atype):
        self.id = id
        self.fname = fname
        self.lname = lname
        self.email = email
        self.pw = pw
        self.type = atype

    def check_password(self, pw):
        return bcrypt.checkpw(pw.encode("utf-8"), self.pw)

    def __str__(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "fname": self.fname,
                "lname": self.lname,
                "email": self.email,
                "pw": str(self.pw),
                "type": self.type,
            }
        )
