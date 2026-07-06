# 09_DATABASE_ARCHITECTURE.md
Version 1.0
Status: LOCKED

## 1. Introduction
While version 1.0 of OmniVision relies on the file system for static storage (images, audio) and ephemeral session state, version 2.0 introduces a robust PostgreSQL database to support historical tracking, user authentication, and analytics. This document outlines the schema design and ORM strategy for future database integration.

## 2. Architecture & ORM Strategy
- **RDBMS**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (Async Engine)
- **Migrations**: Alembic

By using SQLAlchemy's async capabilities (`asyncpg` driver), the FastAPI backend remains non-blocking during database operations.

## 3. Entity Relationship Diagram (ERD)

```text
+---------------+       +------------------+
|    users      |       |  knowledge_packs |
|---------------|       |------------------|
| id (UUID) PK  |       | id (UUID) PK     |
| username      |       | name             |
| email         |       | version          |
| password_hash |       | total_entries    |
| created_at    |       | created_at       |
+-------+-------+       +--------+---------+
        |                        |
        | 1:N                    | 1:N
        v                        v
+-------+-------+       +--------+---------+
|    images     |       |   retrievals     |
|---------------|       |------------------|
| id (UUID) PK  |<------| id (UUID) PK     |
| user_id FK    |       | caption_id FK    |
| image_path    |       | pack_id FK       |
| upload_time   |       | similarity_score |
+-------+-------+       | context_used     |
        |               +------------------+
        | 1:1
        v
+---------------+
|   captions    |
|---------------|
| id (UUID) PK  |
| image_id FK   |
| raw_caption   |
| grounded      |
| final_caption |
+-------+-------+
        |
        | 1:N
        v
+---------------+
| translations  |
|---------------|
| id (UUID) PK  |
| caption_id FK |
| language      |
| text          |
| audio_path    |
+---------------+
```

## 4. SQL Schema Definitions

### 4.1 Users Table
Stores authenticated user credentials.
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 4.2 Images Table
Tracks uploaded images and maps them to a user.
```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_images_user_id ON images(user_id);
```

### 4.3 Captions Table
Stores the results of the BLIP and Grounding pipelines.
```sql
CREATE TABLE captions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID UNIQUE REFERENCES images(id) ON DELETE CASCADE,
    raw_caption TEXT NOT NULL,
    is_grounded BOOLEAN DEFAULT FALSE,
    final_caption TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 Translations & Audio Table
Consolidates translation text and the resulting TTS audio paths.
```sql
CREATE TABLE translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caption_id UUID REFERENCES captions(id) ON DELETE CASCADE,
    language_code VARCHAR(10) NOT NULL,  -- e.g., 'hi', 'te'
    translated_text TEXT NOT NULL,
    audio_file_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(caption_id, language_code)
);
```

### 4.5 Knowledge Packs & Retrievals (Audit Logs)
Used to audit the RAG performance and track which facts were injected.
```sql
CREATE TABLE knowledge_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pack_name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retrievals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caption_id UUID REFERENCES captions(id) ON DELETE CASCADE,
    knowledge_pack_id UUID REFERENCES knowledge_packs(id),
    retrieved_text TEXT NOT NULL,
    similarity_score NUMERIC(5, 4) NOT NULL,
    threshold_applied NUMERIC(5, 4) NOT NULL
);
```

## 5. Security & Privacy Considerations
- **Image Storage**: The database only stores paths to images. The physical files reside in an S3-compatible object store (or local `/static` block). 
- **Data Deletion**: `ON DELETE CASCADE` is applied to ensure that if a user deletes their account, all associated images, captions, and translations are instantly purged to comply with privacy best practices.
- **Password Hashing**: `bcrypt` will be utilized inside the Python application layer before inserting `password_hash` into PostgreSQL.
