#!/usr/bin/env python3
"""Database management script."""

import os
import sys
import click
from flask import Flask
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Creator, Transaction, Withdrawal, TipLink

app = create_app()

@click.group()
def cli():
    """Management script for the application."""
    pass

@cli.command()
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        click.echo('Database initialized successfully.')

@cli.command()
def drop_db():
    """Drop all tables."""
    with app.app_context():
        db.drop_all()
        click.echo('Database tables dropped successfully.')

@cli.command()
def reset_db():
    """Reset the database."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        click.echo('Database reset successfully.')

@cli.command()
@click.argument('username')
@click.argument('password')
@click.option('--name', default=None, help='Creator display name')
@click.option('--phone-number', default=None, help='Creator phone number')
def create_creator(username, password, name=None, phone_number=None):
    """Create a new creator."""
    with app.app_context():
        creator = Creator(username=username, display_name=name, phone_number=phone_number)
        creator.set_password(password)
        db.session.add(creator)
        db.session.commit()
        
        # Create a default tip link
        tip_link = TipLink(slug=username.lower(), creator_id=creator.id)
        db.session.add(tip_link)
        db.session.commit()
        
        click.echo(f'Creator {username} created successfully with tip link: {tip_link.slug}')

@cli.command()
def list_creators():
    """List all creators."""
    with app.app_context():
        creators = Creator.query.all()
        if not creators:
            click.echo('No creators found.')
            return
            
        for creator in creators:
            click.echo(f'ID: {creator.id}, Username: {creator.username}, Display Name: {creator.display_name}, Active: {creator.active}')

if __name__ == '__main__':
    cli() 