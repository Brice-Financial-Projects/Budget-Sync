# budget_sync/cli.py

import click
from flask.cli import with_appcontext
from src.budget_sync import db
from src.budget_sync import StateInfo, StateTaxBracket


@click.group()
def tax_cli():
    """Tax rate management commands."""
    pass


@tax_cli.command()
@with_appcontext
def init_states():
    """Initialize the states table with all US states."""
    states = [
        ('AL', 'Alabama', True),
        ('AK', 'Alaska', False),
        ('AZ', 'Arizona', True),
        # ... add all other states
        ('WY', 'Wyoming', False)
    ]

    for state_code, state_name, has_tax in states:
        state = StateInfo(
            state_code=state_code,
            state_name=state_name,
            has_state_tax=has_tax
        )
        db.session.add(state)

    try:
        db.session.commit()
        click.echo('Successfully initialized states table.')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error initializing states: {str(e)}', err=True)


@tax_cli.command()
@click.argument('state')
@click.argument('year', type=int)
@with_appcontext
def add_tax_brackets(state, year):
    """Add tax brackets for a specific state and year."""
    # First verify the state exists
    state = state.upper()
    state_info = StateInfo.query.filter_by(state_code=state).first()

    if not state_info:
        click.echo(f'Error: State {state} not found', err=True)
        return

    if not state_info.has_state_tax:
        click.echo(f'Note: {state} has no state income tax')
        return

    click.echo(f'Adding tax brackets for {state} {year}')

    # Get brackets from user input
    brackets = []
    while True:
        if not click.confirm('Add another bracket?'):
            break

        bracket_floor = click.prompt('Enter bracket floor', type=float)
        rate = click.prompt('Enter tax rate (as decimal)', type=float)

        bracket = StateTaxBracket(
            state=state,
            tax_year=year,
            bracket_floor=bracket_floor,
            rate=rate
        )
        brackets.append(bracket)

    try:
        db.session.bulk_save_objects(brackets)
        db.session.commit()
        click.echo(f'Successfully added {len(brackets)} tax brackets for {state} {year}')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error adding tax brackets: {str(e)}', err=True)


@tax_cli.command()
@click.argument('state')
@click.argument('year', type=int)
@with_appcontext
def view_tax_brackets(state, year):
    """View tax brackets for a specific state and year."""
    state = state.upper()
    brackets = StateTaxBracket.query \
        .filter_by(state=state, tax_year=year) \
        .order_by(StateTaxBracket.bracket_floor) \
        .all()

    if not brackets:
        click.echo(f'No tax brackets found for {state} {year}')
        return

    click.echo(f'\nTax Brackets for {state} {year}:')
    for bracket in brackets:
        click.echo(f'Floor: ${bracket.bracket_floor:,.2f} - Rate: {bracket.rate * 100:.2f}%')


def init_app(app):
    """Register CLI commands with the budget_sync."""
    app.cli.add_command(tax_cli)

