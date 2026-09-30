import pandas as pd
from sqlalchemy import create_engine

ENGINE = create_engine(
    "mysql+pymysql://root:pass@127.0.0.1:3306/cafe"
)


def q(sql: str, **kwargs) -> pd.DataFrame:
    return pd.read_sql(sql, ENGINE, **kwargs)