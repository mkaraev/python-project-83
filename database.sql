DROP TABLE IF EXISTS url_checks CASCADE;
DROP TABLE IF EXISTS urls CASCADE;
CREATE TABLE urls
(
    id         SERIAL,
    name       VARCHAR(255) UNIQUE,
    created_at DATE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE url_checks
(
    id          SERIAL,
    url_id      INTEGER,
    status_code INTEGER,
    h1          VARCHAR(255),
    title       VARCHAR(255),
    description VARCHAR(255),
    created_at  DATE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (url_id) REFERENCES urls (id) ON DELETE CASCADE ON UPDATE CASCADE
);