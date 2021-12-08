# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.


import pickle
import sqlite3
global db


db = sqlite3.connect('../assets/database/sessions.sqlite', isolation_level=None, timeout=10)
db.text_factory = str
sqlite3.register_adapter(dict, lambda d: pickle.dumps(d))
sqlite3.register_converter("dictionary", lambda d: pickle.loads(d))

