from argparse import Namespace
from devpi.push import main as devpi_push


def get_available_indices(hub):
    root_url = hub.current.root_url
    r = hub.http_api("get", root_url, quiet=True, check_version=False)
    return r.result


def push(hub, args):
    # TODO: local imports to avoid circular dependencies, can clean-up once Poetry's plugin system arrives
    from poetry.packages.locker import Locker
    from tomlkit.toml_file import TOMLFile

    current_index = hub.current.index
    root_url = hub.current.root_url.url
    current_user, current_index = current_index[len(root_url):].split('/')
    available_indices = hub.http_api("get", root_url, quiet=True, check_version=False).result

    local_config = TOMLFile('pyproject.toml').read()
    locker = Locker('poetry.lock', local_config)
    locked_repository = locker.locked_repository(with_dev_reqs=not args.no_dev)

    for pkg in locked_repository.packages:
        name, version = pkg.name, pkg.version.text
        if pkg.source_url and pkg.source_url != current_index:
            hub.warn(
                "'{}=={}' is locked from {} which is not the current index, skipping.".format(
                    name, version, pkg.source_url
                )
            )
            continue

        # try to guess the index from the download link
        project_url = hub.current.get_project_url(name)
        reply = hub.http_api("get", project_url, type="projectconfig")
        link = reply.result.get(version, {}).get('+links', [{}])[0].get('href')

        if not link.startswith(root_url):
            hub.warn(
                "'{}=={}' is mirrored from an external url, skipping.".format(name, version)
            )
            continue

        user, index, _ = link[len(root_url):].split('/', 2)
        if (
                (user, index) != (current_user, current_index)
                and not args.include_local_bases
                and available_indices.get(user, {}).get('indexes', {}).get(index, {}).get('type') != 'mirror'
        ):
            hub.info("Skipping '{}=={}' available from local base '{}/{}'".format(name, version, user, index))
            continue

        pkg_args = Namespace(
            pkgspec='{}=={}'.format(name, version), index='{}/{}'.format(user, index), **vars(args)
        )
        devpi_push(hub, pkg_args)


def push_arguments(parser):
    """ push all packages from poetry lock-file to an internal or external index.
        You can push a release with all its release files either
        to an external pypi server ("pypi:REPONAME") where REPONAME
        needs to be defined in your ``.pypirc`` file.  Or you can
        push to another devpi index ("user/name").
    """
    parser.add_argument("--pypirc", metavar="path", type=str,
        default=None, action="store",
        help="path to pypirc")
    parser.add_argument("--no-dev", default=False, action="store_true",
                        help="do not push dev dependencies")
    parser.add_argument("--include-local-bases", default=False, action="store_true",
                        help="push dependencies from non-mirror base indices as well")
    parser.add_argument("target", metavar="TARGETSPEC", type=str,
        action="store",
        help="local or remote target index. local targets are of form "
             "'USER/NAME', specifying an existing writeable local index. "
             "remote targets are of form 'REPO:' where REPO must be an "
             "existing entry in the pypirc file.")
