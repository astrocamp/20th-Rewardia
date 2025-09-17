import subprocess


def get_git_commit_hash():
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "dev"


STATIC_VERSION_HASH = get_git_commit_hash()

def version(request):
    return {"STATIC_VERSION": STATIC_VERSION_HASH}
