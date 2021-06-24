# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

from wtforms import RadioField


class HelloForm(FlaskForm):
    # name = StringField('Name', validators=[DataRequired(), Length(1, 20)])
    c_type = StringField('', validators=[DataRequired(), Length(1, 20)])
    body_textarea = TextAreaField(' ', validators=[DataRequired(), Length(1, 200)])
    submit_btn = SubmitField(label='提交')




