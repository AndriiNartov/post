from post_site import db


class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(10), unique=True, nullable=False)
    letters = db.relationship('Letter', backref='truck', lazy=True)

    def __str__(self):
        return self.plate_number

    def __repr__(self):
        return self.plate_number


class Letter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sending_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    status_date = db.Column(db.Date, nullable=False)
    track_number = db.Column(db.String(20), unique=True, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)

    def __str__(self):
        return self.track_number

    def __repr__(self):
        return self.track_number
