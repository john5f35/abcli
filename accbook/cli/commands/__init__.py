import os
import logging
import importlib

logger = logging.getLogger()

def init_command_groups(root):
    src_files = list(filter(lambda name: not name.startswith("__"), \
                            os.listdir(os.path.dirname(__file__))))
    for pysrc in src_files:
        try:
            mod_name = f'.{pysrc[:pysrc.index(".py")]}'
            mod = importlib.import_module(mod_name, __name__)
            cli = getattr(mod, 'cli')
            root.add_command(cli)
        except Exception:
            logger.warning(f"Skipped {pysrc} when searching for sub-command groups")
