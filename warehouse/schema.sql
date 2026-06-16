-- Dimension tables
CREATE TABLE dim_age (
    age_id      INTEGER PRIMARY KEY,
    age_group   VARCHAR NOT NULL,    -- '0-17', '18-29', etc.
    age_min     INTEGER,
    age_max     INTEGER
);

CREATE TABLE dim_gender (
    gender_id   INTEGER PRIMARY KEY,
    gender      VARCHAR NOT NULL     -- 'Male', 'Female', 'Unknown'
);

CREATE TABLE dim_race (
    race_id     INTEGER PRIMARY KEY,
    race        VARCHAR NOT NULL
);

CREATE TABLE dim_vaccine (
    vaccine_id      INTEGER PRIMARY KEY,
    vax_name        VARCHAR,
    manufacturer    VARCHAR,         -- 'Pfizer', 'Moderna', 'Janssen', 'Other/Unknown'
    vax_type        VARCHAR
);

CREATE TABLE dim_symptom (
    symptom_id  INTEGER PRIMARY KEY,
    symptom     VARCHAR NOT NULL UNIQUE
);

CREATE TABLE dim_location (
    location_id INTEGER PRIMARY KEY,
    state_code  VARCHAR(2),
    state_name  VARCHAR,
    region      VARCHAR
);

-- Fact tables
CREATE TABLE fact_covid_cases (
    case_id         BIGINT PRIMARY KEY,
    case_month      DATE,
    location_id     INTEGER REFERENCES dim_location(location_id),
    age_id          INTEGER REFERENCES dim_age(age_id),
    gender_id       INTEGER REFERENCES dim_gender(gender_id),
    race_id         INTEGER REFERENCES dim_race(race_id),
    hosp_yn         TINYINT,         -- 1/0/null
    icu_yn          TINYINT,
    death_yn        TINYINT,
    underlying_yn   TINYINT
);

CREATE TABLE fact_vaccine_events (
    event_id        BIGINT PRIMARY KEY,
    vaers_id        BIGINT NOT NULL,
    rpt_date        DATE,
    age_id          INTEGER REFERENCES dim_age(age_id),
    gender_id       INTEGER REFERENCES dim_gender(gender_id),
    location_id     INTEGER REFERENCES dim_location(location_id),
    vaccine_id      INTEGER REFERENCES dim_vaccine(vaccine_id),
    died            TINYINT,
    hospital        TINYINT,
    disable         TINYINT,
    recovered       TINYINT,
    er_visit        TINYINT,
    onset_days      INTEGER
);

CREATE TABLE fact_vaccine_symptoms (
    vaers_id    BIGINT,
    symptom_id  INTEGER REFERENCES dim_symptom(symptom_id),
    PRIMARY KEY (vaers_id, symptom_id)
);

CREATE TABLE fact_hospital_capacity (
    capacity_id         BIGINT PRIMARY KEY,
    collection_week     DATE,
    location_id         INTEGER REFERENCES dim_location(location_id),
    covid_inpatient     INTEGER,
    covid_icu           INTEGER,
    covid_admissions    INTEGER
);

CREATE TABLE fact_mortality (
    mortality_id    BIGINT PRIMARY KEY,
    period_start    DATE,
    period_end      DATE,
    location_id     INTEGER REFERENCES dim_location(location_id),
    age_id          INTEGER REFERENCES dim_age(age_id),
    gender_id       INTEGER REFERENCES dim_gender(gender_id),
    covid_deaths    INTEGER,
    total_deaths    INTEGER
);
