db = db.getSiblingDB('db_romain');
db.createUser({ user: "romain", pwd: process.env.ROMAIN_PASSWORD, roles: [{ role: "dbOwner", db: "db_romain" }] });

db = db.getSiblingDB('db_nahed');
db.createUser({ user: "nahed", pwd: process.env.NAHED_PASSWORD, roles: [{ role: "dbOwner", db: "db_nahed" }] });

db = db.getSiblingDB('db_belkacem');
db.createUser({ user: "belkacem", pwd: process.env.BELKACEM_PASSWORD, roles: [{ role: "dbOwner", db: "db_belkacem" }] });

db = db.getSiblingDB('db_velib');
db.createUser({ user: "velib", pwd: process.env.VELIB_PASSWORD, roles: [{ role: "dbOwner", db: "db_velib" }] });
