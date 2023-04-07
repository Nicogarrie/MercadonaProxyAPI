import pandas as pd
import sqlalchemy as sql
import sqlalchemy.engine as sql_engine

import configs
import tables

POSTGRES = "Postgres"
EMERGENCY_FILEPATH = "emergency_save.csv"


class EngineCreationException(Exception):
    """
    Raised when an exception happened while creating a database engine
    """


class TableCreationException(Exception):
    """
    Raised when an exception happened while creating tables
    """


class SQLEngine:
    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int,
        database: str,
        drivername: str,
    ) -> None:
        try:
            self.connection_url = sql_engine.URL.create(
                drivername=drivername,
                username=username,
                password=password,
                host=host,
                port=port,
                database=database,
            )
            self.engine = sql.create_engine(self.connection_url)
        except Exception as engine_error:
            raise EngineCreationException(
                f"There was a problem trying to connect with the database: {str(engine_error)}"
            ) from engine_error

        try:
            tables.Base.metadata.create_all(self.engine)
        except Exception as table_error:
            raise TableCreationException(
                f"There was a problem creating new tables in the database: {str(table_error)}"
            ) from table_error

    def store_df_in_table(self, table_name: str, dataframe: pd.DataFrame) -> None:
        dataframe.to_sql(
            name=table_name, con=self.engine, if_exists="replace", index=False
        )

    def store_csv_in_table(self, table_name: str, csv_filepath: str) -> None:
        dataframe = pd.read_csv(csv_filepath)
        self.store_df_in_table(table_name, dataframe)


class PostgresEngine(SQLEngine):
    def __init__(self) -> None:
        postgres_config = configs.init_postgres()

        username = postgres_config["username"]
        password = postgres_config["password"]
        host = postgres_config["host"]
        port = int(postgres_config["port"])
        database = postgres_config["database"]

        super().__init__(
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
            drivername="postgresql+psycopg2",
        )


def save_df_in_database(
    table_name: str,
    dataframe: pd.DataFrame,
    database_engine: str = POSTGRES,
    emergency_save_filepath: str = EMERGENCY_FILEPATH,
) -> None:
    print(f"Storing dataframe in table {table_name}...")
    try:
        if database_engine == POSTGRES:
            db_engine = PostgresEngine()
        else:
            raise ValueError("Unsupported database engine")

        db_engine.store_df_in_table(table_name, dataframe)
        print("Success!")
    except Exception as database_error:
        print(f"An error happened while working with the database: {database_error}")
        print(
            f"Trying to create an emergency csv to save the data in {emergency_save_filepath}..."
        )
        dataframe.to_csv(emergency_save_filepath, index=False)


def save_csv_in_database(
    table_name: str,
    csv_filepath: str,
    database_engine: str = POSTGRES,
) -> None:
    print(f"Storing csv in table {table_name}...")
    try:
        if database_engine == POSTGRES:
            db_engine = PostgresEngine()
        else:
            raise ValueError("Unsupported database engine")

        db_engine.store_csv_in_table(table_name, csv_filepath)
        print("Success!")
    except Exception as database_error:
        print(f"An error happened while working with the database: {database_error}")
