import click

from theatre.app import create_app


@click.command()
@click.option(
    "--database", required=True, help="The path to the SQLite database to use."
)
def main(database: str):
    app = create_app(database)
    app.run()


if __name__ == "__main__":
    main()
