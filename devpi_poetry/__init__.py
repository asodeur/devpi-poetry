from pluggy import HookimplMarker
from .devpi_push import push_arguments

client_hookimpl = HookimplMarker("devpiclient")

@client_hookimpl
def devpiclient_subcommands():
    return [
        (push_arguments, "poetry-push", "devpi_poetry.devpi_push:push"),
    ]