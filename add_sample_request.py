import sqlite3

con = sqlite3.connect("accounts.sqlite")
cur = con.cursor()

cur.execute(
    #     """INSERT INTO requests (attorney_id, ISBN, prison_title)
    # VALUES
    #     (1, '1931498717', 'San Mateo County Jail'),
    #     (2, '1931498717', 'San Francisco Penitentiary');"""
    """DELETE FROM requests WHERE rowid=3;"""
)
con.commit()
con.close()
