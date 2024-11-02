CREATE SCHEMA ls

CREATE TABLE KBAs (
    SAP_Component NVARCHAR(255),
    Document_Id NVARCHAR(20) PRIMARY KEY,
    Version INT,
    Title NVARCHAR(255),
    Category NVARCHAR(100),
    Priority NVARCHAR(50),
    Released_On DATE,
    Link NVARCHAR(255)
);

CREATE TABLE Embeddings (
    Chunk_Id NVARCHAR(150) PRIMARY KEY,
    Document_Id NVARCHAR(100) NOT NULL,
    Section NVARCHAR(100),
    Text NCLOB,
    Embedding REAL_VECTOR,
    FOREIGN KEY (Document_Id) REFERENCES kbas(Document_Id)
);
CREATE INDEX idx_doc_id ON Embeddings(Document_Id);
CREATE INDEX idx_section ON Embeddings(Section);