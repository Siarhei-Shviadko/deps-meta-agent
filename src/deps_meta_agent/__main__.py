import click

from deps_meta_agent.entrypoint import run_api, run_message_dispatcher


@click.group()
def cli() -> None:
    pass


@click.command()
def serve() -> None:
    run_api()


@click.command()
def dispatch() -> None:
    run_message_dispatcher()


if __name__ == "__main__":
    cli.add_command(serve)
    cli.add_command(dispatch)
    cli()
