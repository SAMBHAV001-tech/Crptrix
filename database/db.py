from sqlalchemy import create_engine

DATABASE_URL = "postgresql://crptrix_user:2tN5cuFSgoDFiC2A0lDCkbNvXJ3md2Ag@dpg-d5l52ap4tr6s738f07ag-a.singapore-postgres.render.com/crptrix"

engine = create_engine(DATABASE_URL, echo=False)
