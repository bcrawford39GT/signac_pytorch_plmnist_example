"""Setup the HPC and custom template location"""

from flow.environment import DefaultSlurmEnvironment


class Phoenix(DefaultSlurmEnvironment):
    """Subclass of DefaultSlurmEnvironment for GT Phoenix HPC."""

    # Find the hostname by loggin in the HPC and using the 'hostname' command.
    # In this case 'hostname' produced 'login-phoenix-rh9--2.pace.gatech.edu'.
    hostname_pattern = r"login-phoenix-rh9-.\.pace\.gatech\.edu"
    template = "phoenix.sh"

    # NOTE: we never actually import this class ourselves - Signac looks at all
    # defined environment classes and runs `EnvironmentClass.is_present()`
    # and uses one which returns True.
