# -*- coding: utf-8 -*-

from datetime import datetime

from sayhello import db


class Message(db.Model):

    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    c_type = db.Column(db.String(20))
    body = db.Column(db.String(200))
    nl_body = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
