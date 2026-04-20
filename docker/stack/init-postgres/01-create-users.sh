#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL

    CREATE USER romain WITH PASSWORD '${ROMAIN_PASSWORD}';
    CREATE USER nahed WITH PASSWORD '${NAHED_PASSWORD}';
    CREATE USER belkacem WITH PASSWORD '${BELKACEM_PASSWORD}';
    CREATE USER velib WITH PASSWORD '${VELIB_PASSWORD}';

    CREATE DATABASE db_romain OWNER romain;
    CREATE DATABASE db_nahed OWNER nahed;
    CREATE DATABASE db_belkacem OWNER belkacem;
    CREATE DATABASE db_velib OWNER velib;

EOSQL
