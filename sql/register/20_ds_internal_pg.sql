CREATE DATASOURCE internal_pg OPTIONS (jdbcurl "jdbc:postgresql://pi-postgres:5432/agency_internal", jdbcdriver "org.postgresql.Driver", username "${POSTGRES_USER}", password "${POSTGRES_PASSWORD}")
