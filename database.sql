CREATE DATABASE cadastro_gov;
USE cadastro_gov;

-- Tabela de login
CREATE TABLE cadastro_login (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE login_adm (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE cadastro_pessoas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    idade INT NOT NULL,
    genero VARCHAR(50) NOT NULL,
    endereco_completo TEXT NOT NULL,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    renda_familiar_mensal DECIMAL(10,2) NOT NULL,
    numero_membros_familia INT NOT NULL,
    despesas_mensais DECIMAL(10,2) NOT NULL,
    nivel_escolaridade VARCHAR(100) NOT NULL,
    outras_informacoes TEXT,
    status ENUM('Pendente', 'Aprovado', 'Rejeitado') DEFAULT 'Pendente'
);

INSERT INTO cadastro_login (nome_completo, email, senha)
VALUES ('teste', 'testen@example.com', SHA2('senha123', 256));
