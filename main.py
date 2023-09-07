import sqlalchemy as db
engine = db.create_engine("postgresql://postgres:mysecretpassword@localhost:5432/sysml2")

conn = engine.connect()

metadata = db.MetaData()

Models = db.Table('Models', metadata,
          db.Column('Id', db.Integer(), primary_key=True),
          db.Column('Name', db.String(255), nullable=False),
          db.Column('Commit', db.String(255), nullable=False),
          db.Column('Ref', db.String(255), nullable=False),
          db.Column('Date', db.DateTime(), nullable=False)
)



metadata.create_all(engine)
