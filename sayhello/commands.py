# -*- coding: utf-8 -*-

import click

from sayhello import app, db
from sayhello.models import Message


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        click.confirm('This operation will delete the database, do you want to continue?', abort=True)
        db.drop_all()
        click.echo('Drop tables.')
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
@click.option('--count', default=1, help='Quantity of messages, default is 20.')
def forge(count):
    """Generate fake messages."""
    from faker import Faker

    db.drop_all()
    db.create_all()
    print("Dropped!")

    fake = Faker()
    click.echo('Working...')

    for i in range(count):
        message = Message(
            # name=fake.name(),
            body="None",
            c_type="None",
            nl_body="None",
            timestamp=fake.date_time_this_year()
        )
        print(message)
        db.session.add(message)

    db.session.commit()
    click.echo('Created %d fake messages.' % count)
