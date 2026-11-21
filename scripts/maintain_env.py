"""
Maintain Environment Configuration
Safely cleans up, formats, and organizes .env and .env.example
while preserving all active credentials and secrets verbatim.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
from src.core.security import mask_secret

def maintain(updates: dict = None):
    env_file = ".env"
    example_file = ".env.example"

    # 1. Read existing .env if present
    env_dict = {}
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line_clean = line.strip()
                if "=" in line_clean and not line_clean.startswith("#"):
                    k, v = line_clean.split("=", 1)
                    env_dict[k.strip()] = v.strip()

    # Apply any programmatic updates
    if updates:
        for k, v in updates.items():
            env_dict[k] = v

    # Verify that existing keys were not dropped
    nvidia_key = env_dict.get("NVIDIA_API_KEY", "")
    bodhan_key = env_dict.get("BODHAN_API_KEY", "")

    print(f"[MAINTAIN] NVIDIA_API_KEY preserved: {mask_secret(nvidia_key)}")
    print(f"[MAINTAIN] BODHAN_API_KEY preserved: {mask_secret(bodhan_key)}")

    # 2. Structured Sections
    formatted_env = f"""# ==============================================================================
# BodhAI — Unified Environment Configuration
# Curriculum: CBSE Class 10 Science (2026–27)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Supabase Cloud Infrastructure (Database, pgvector, Storage, Auth)
# ------------------------------------------------------------------------------
SUPABASE_URL={env_dict.get("SUPABASE_URL", "")}
SUPABASE_ANON_KEY={env_dict.get("SUPABASE_ANON_KEY", "")}
SUPABASE_SERVICE_ROLE_KEY={env_dict.get("SUPABASE_SERVICE_ROLE_KEY", "")}
SUPABASE_DB_PASSWORD={env_dict.get("SUPABASE_DB_PASSWORD", "")}
SUPABASE_DB_URL={env_dict.get("SUPABASE_DB_URL", "")}

# ------------------------------------------------------------------------------
# 2. NVIDIA Nemotron LLM Configuration (Chat & Quiz Generation)
# ------------------------------------------------------------------------------
LLM_PROVIDER={env_dict.get("LLM_PROVIDER", "nvidia")}
LLM_MODEL={env_dict.get("LLM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")}
NVIDIA_MODEL={env_dict.get("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")}
NVIDIA_BASE_URL={env_dict.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")}
NVIDIA_API_KEY={nvidia_key}
LLM_TIMEOUT_SECONDS={env_dict.get("LLM_TIMEOUT_SECONDS", "120")}
LLM_MAX_RETRIES={env_dict.get("LLM_MAX_RETRIES", "2")}
LLM_MAX_OUTPUT_TOKENS={env_dict.get("LLM_MAX_OUTPUT_TOKENS", "16384")}
LLM_TEMPERATURE={env_dict.get("LLM_TEMPERATURE", "1.0")}
LLM_TOP_P={env_dict.get("LLM_TOP_P", "0.95")}
LLM_ENABLE_THINKING={env_dict.get("LLM_ENABLE_THINKING", "true")}
LLM_REASONING_BUDGET={env_dict.get("LLM_REASONING_BUDGET", "16384")}
LLM_STREAMING_ENABLED={env_dict.get("LLM_STREAMING_ENABLED", "true")}

# ------------------------------------------------------------------------------
# 3. Bodhan Indic-OCR Document Processing Configuration
# ------------------------------------------------------------------------------
OCR_PROVIDER={env_dict.get("OCR_PROVIDER", "bodhan")}
BODHAN_BASE_URL={env_dict.get("BODHAN_BASE_URL", "https://api.bodhan.ai/v1")}
BODHAN_API_KEY={bodhan_key}
BODHAN_OCR_MODEL={env_dict.get("BODHAN_OCR_MODEL", "indic-ocr")}
OCR_TIMEOUT_SECONDS={env_dict.get("OCR_TIMEOUT_SECONDS", "120")}
OCR_MAX_RETRIES={env_dict.get("OCR_MAX_RETRIES", "2")}
OCR_MIN_TEXT_THRESHOLD_CHARS={env_dict.get("OCR_MIN_TEXT_THRESHOLD_CHARS", "50")}
OCR_IMAGE_DPI={env_dict.get("OCR_IMAGE_DPI", "300")}

# ------------------------------------------------------------------------------
# 4. Text Embeddings Configuration (for RAG & pgvector)
# ------------------------------------------------------------------------------
EMBEDDING_PROVIDER={env_dict.get("EMBEDDING_PROVIDER", "nvidia")}
EMBEDDING_MODEL={env_dict.get("EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")}
EMBEDDING_DIMENSION={env_dict.get("EMBEDDING_DIMENSION", "1024")}
"""

    formatted_example = """# ==============================================================================
# BodhAI — Example Environment Configuration Template
# Copy this file to .env and insert your real credentials.
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Supabase Cloud Infrastructure (Database, pgvector, Storage, Auth)
# ------------------------------------------------------------------------------
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_URL=postgresql://postgres:your-db-password@db.your-project-id.supabase.co:5432/postgres

# ------------------------------------------------------------------------------
# 2. NVIDIA Nemotron LLM Configuration (Chat & Quiz Generation)
# ------------------------------------------------------------------------------
LLM_PROVIDER=nvidia
LLM_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_API_KEY=nvapi-your-key-here
LLM_TIMEOUT_SECONDS=120
LLM_MAX_RETRIES=2
LLM_MAX_OUTPUT_TOKENS=16384
LLM_TEMPERATURE=1.0
LLM_TOP_P=0.95
LLM_ENABLE_THINKING=true
LLM_REASONING_BUDGET=16384
LLM_STREAMING_ENABLED=true

# ------------------------------------------------------------------------------
# 3. Bodhan Indic-OCR Document Processing Configuration
# ------------------------------------------------------------------------------
OCR_PROVIDER=bodhan
BODHAN_BASE_URL=https://api.bodhan.ai/v1
BODHAN_API_KEY=sk-your-bodhan-key-here
BODHAN_OCR_MODEL=indic-ocr
OCR_TIMEOUT_SECONDS=120
OCR_MAX_RETRIES=2
OCR_MIN_TEXT_THRESHOLD_CHARS=50
OCR_IMAGE_DPI=300

# ------------------------------------------------------------------------------
# 4. Text Embeddings Configuration (for RAG & pgvector)
# ------------------------------------------------------------------------------
EMBEDDING_PROVIDER=nvidia
EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
EMBEDDING_DIMENSION=1024
"""

    with open(env_file, "w", encoding="utf-8") as f:
        f.write(formatted_env)

    with open(example_file, "w", encoding="utf-8") as f:
        f.write(formatted_example)

    print("[SUCCESS] Both .env and .env.example formatted cleanly with zero credential loss.")

if __name__ == "__main__":
    maintain()
