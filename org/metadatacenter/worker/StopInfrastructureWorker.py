from rich.console import Console

from org.metadatacenter.util.GlobalContext import GlobalContext
from org.metadatacenter.util.Util import Util
from org.metadatacenter.worker.Worker import Worker

console = Console()


class StopInfrastructureWorker(Worker):

    def __init__(self):
        super().__init__()

    @staticmethod
    def all():
        if GlobalContext.get_use_osa():
            Worker.execute_generic_shell_commands(
                ["osascript " + Util.get_osa_script_path('stop-infrastructure.scpt')],
                title="Stopping Infrastructure services",
            )
        else:
            Worker.execute_generic_shell_commands(
                ["source " + Util.get_bash_script_path('stop-infrastructure.sh')],
                title="Stopping Infrastructure services",
            )
