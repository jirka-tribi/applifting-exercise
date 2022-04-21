CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_pwd BYTEA NOT NULL
);

CREATE TABLE IF NOT EXISTS products(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS offers(
    id INT PRIMARY KEY,
    product_id INT NOT NULL,
    price INT NOT NULL,
    items_in_stock INT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);
