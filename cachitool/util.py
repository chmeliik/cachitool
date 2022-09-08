import logging
import os.path
import subprocess
import urllib
from pathlib import Path

from cachitool.errors import SubprocessCallError, CachitoCalledProcessError


log = logging.getLogger(__name__)


def normpath(path: str | Path) -> Path:
    return Path(os.path.normpath(path))


def get_repo_name(url: str) -> str:
    """Get the repo name from the URL."""
    parsed_url = urllib.parse.urlparse(url)
    repo = parsed_url.path.strip("/")
    if repo.endswith(".git"):
        repo = repo[: -len(".git")]
    return repo


def run_cmd(cmd, params, exc_msg=None):
    """
    Run the given command with provided parameters.

    :param iter cmd: iterable representing command to be executed
    :param dict params: keyword parameters for command execution
    :param str exc_msg: an optional exception message when the command fails
    :returns: the command output
    :rtype: str
    :raises SubprocessCallError: if the command fails
    """
    params.setdefault("capture_output", True)
    params.setdefault("universal_newlines", True)
    params.setdefault("encoding", "utf-8")

    # conf = get_worker_config()
    # params.setdefault("timeout", conf.cachito_subprocess_timeout)
    params.setdefault("timeout", 900)  # 15 minutes

    try:
        response = subprocess.run(cmd, **params)  # nosec
    except subprocess.TimeoutExpired as e:
        raise SubprocessCallError(str(e))

    if response.returncode != 0:
        log.error('The command "%s" failed with: %s', " ".join(cmd), response.stderr)
        raise CachitoCalledProcessError(
            exc_msg or "An unexpected error occurred", response.returncode
        )

    return response.stdout
