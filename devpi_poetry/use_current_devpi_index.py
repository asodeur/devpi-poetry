# TODO: currently this requires a patched poetry>=1.0.0a4 but we hope this can be hooked into poetry's plugin
#  system once that becomes available

from argparse import ArgumentParser
from devpi.main import add_generic_options, Hub


def _get_devpi_args(argv):
    parser = ArgumentParser()
    add_generic_options(parser, defaults=True)
    return parser.parse_args(argv)

def use_current_devpi_index(event, event_name, _):  # type: (PreHandleEvent, str, _) -> None
    # TODO: local import to avoid circular dependencies, clean-up once Poetry's plug-in systems arrives
    from poetry.repositories.legacy_repository import LegacyRepository

    # TODO: this hook is fired too late, we need to mutating Repository._url below. Ideally we would change
    #  repository settings directly after parsing pyproject.toml before the pool is even initialized
    command = event.command.config.handler  # type: EnvCommand
    devpi_args = _get_devpi_args([])
    hub = Hub(devpi_args)
    current_devpi_index = "{}/+simple".format(hub.current.index)

    # replace any repository with the current devpi index, no need for caching as devpi already takes care
    # of this
    if hasattr(command, 'poetry'):
        command.poetry.pool.repositories[:] = [
            LegacyRepository(r.name, current_devpi_index, disable_cache=True) for r in command.poetry.pool.repositories
        ]
        if command.poetry.locker:
            # if we got a lock file, change all package.source to point at the current index
            for info in command.poetry.locker.lock_data.get('package', []):
                source = info.get('source')

                if source and source.get('url', current_devpi_index) != current_devpi_index:
                    event.io.write(
                        "<warning>Package '{}' was installed from '{}' "
                        "which is not the currently active index. "
                        "Will override with current index..</warning>\n".format(info['name'], source['url'])
                    )
                    source['url'] = current_devpi_index
