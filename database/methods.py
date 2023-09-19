import os
import sqlalchemy as db

SQLDEF = "localhost:5432"
SQLHOST = os.environ.get("SQLHOST",SQLDEF)

def connect():
    db_type = "postgresql"
    user = "postgres"
    passwd = "mysecretpassword"
    address = SQLHOST
    db_name = "sysml2"

    address = db_type+"://"+user+":"+passwd+"@"+address+"/"+db_name
    engine = db.create_engine(address)
    conn = engine.connect()

    return conn, engine

def make_tables(engine):
    metadata = db.MetaData()
    if not 'models' in metadata_obj.sorted_tables():
        Models = db.Table('models', metadata,
                  db.Column('id', db.Integer(), primary_key=True),
                  db.Column('name', db.String(255), nullable=False), #notebook id
                  db.Column('ref', db.String(255), nullable=False), # branch
                  db.Column('commit', db.String(255), nullable=False), # commit hash
                  db.Column('nbhash', db.String(255), nullable=False), # notebook path hash
                  db.Column('hash', db.String(255), nullable=False), # model hash
                  db.Column('model', db.String(), nullable=False), # model text
                  db.Column('date', db.DateTime(), nullable=False) # commit date
        )
        metadata.create_all(engine)
