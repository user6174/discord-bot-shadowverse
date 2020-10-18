import asyncio
from Jcg_utils import *


loop = asyncio.get_event_loop()
loop.run_until_complete(update_jcg())
