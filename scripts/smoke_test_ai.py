"""
Optional Smoke Test Script for Live NVIDIA Nemotron & Bodhan OCR APIs
Usage: python scripts/smoke_test_ai.py [--live]
Default: Dry-run checking environment configuration.
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import config
from src.core.security import mask_secret
from src.ai.llm_service import NVIDIANemotronService
from src.ai.ocr_service import BodhanOCRService


def main():
    parser = argparse.ArgumentParser(description="P0.5 AI Infrastructure Smoke Test")
    parser.add_argument("--live", action="store_true", help="Execute real live API requests if credentials exist")
    args = parser.parse_args()

    print("=" * 60)
    print("P0.5 — AI INFRASTRUCTURE SMOKE TEST & CONFIG CHECK")
    print("=" * 60)

    # 1. Inspect NVIDIA Config
    print("\n[1] NVIDIA Nemotron LLM Status:")
    nv_summary = config.nvidia.masked_summary()
    for k, v in nv_summary.items():
        print(f"    - {k}: {v}")

    # 2. Inspect Bodhan Config
    print("\n[2] Bodhan Indic-OCR Status:")
    bd_summary = config.bodhan.masked_summary()
    for k, v in bd_summary.items():
        print(f"    - {k}: {v}")

    if not args.live:
        print("\n[INFO] Dry-run check completed. Live API calls were NOT executed.")
        print("To run live API verification with configured credentials, run:")
        print("  python scripts/smoke_test_ai.py --live")
        return

    # Live test execution if requested
    print("\n[3] Executing Live Smoke Tests...")
    if config.nvidia.is_configured:
        print("--> Testing live NVIDIA Nemotron completion...")
        try:
            llm = NVIDIANemotronService()
            resp = llm.generate([{"role": "user", "content": "Respond with: 'NVIDIA Nemotron Verified'"}])
            print(f"    Success: {resp.content} (latency: {resp.latency_ms}ms)")
        except Exception as e:
            print(f"    Failed: {e}")
    else:
        print("--> NVIDIA API Key not configured; skipping live test.")

    if config.bodhan.is_configured:
        print("--> Testing live Bodhan Indic-OCR completion...")
        try:
            ocr = BodhanOCRService()
            # 1x1 transparent PNG bytes
            png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            resp = ocr.extract_from_image_bytes(png_bytes)
            print(f"    Success: status={resp.get('status')} model={resp.get('model')}")
        except Exception as e:
            print(f"    Failed: {e}")
    else:
        print("--> Bodhan API Key not configured; skipping live test.")


if __name__ == "__main__":
    main()
