# ==> DATABASE CONNECTION..

import psycopg2

def db_connection():
    return psycopg2.connect(
        host = "localhost",
        database = "Stock_Analysis",
        user = "postgres",
        password = "Suhlpga",
        port = 5432
    )
