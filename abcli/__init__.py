# CLI
#
# Commands:
#   - transactions import <json>
#   - transaction show (?)
#   - account show [name] [date-from] [date-to] [aggregation:week|fortnight|*month*|quarter|year]
#       Shows balance, average in aggregation method, between two dates
#   - account graph [name] [date-from] [date-to] [aggregation:...]
#   - budget import <json>
#   - budget show [name] [account]
#       Shows progress & summary of a named budget
#   - budget project [name] [unit] [aggregation:...]

import logging
# logging.basicConfig(format="[%(levelname)s] %(message)s")
import coloredlogs
# TODO: maybe load format from a config file?
coloredlogs.install(fmt="%(message)s", logger=logging.getLogger())
