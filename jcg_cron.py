from Jcg_utils import *

last = scrape_jcg('rotation', 0, True)
if last is not None:
    with open('rotation.json', 'w+') as f:
        json.dump(last, f)
last = scrape_jcg('unlimited', 0, True)
if last is not None:
    with open('unlimited.json', 'w+') as f:
        json.dump(last, f)
