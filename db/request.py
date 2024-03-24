class Request:
    def __init__(self, id, attorney_id, isbn, prison_title, timestamp=None):
        self.id = id
        self.attorney_id = attorney_id
        self.isbn = isbn
        self.prison_title = prison_title
        self.timestamp = timestamp
