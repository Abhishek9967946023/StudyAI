"""
=============================================================================
StudyAI — OCR & Document Processing Django Test Module
=============================================================================
Imports all test cases from testing.unit.test_ocr to allow standard Django
test discovery:
    python manage.py test api.test_ocr
=============================================================================
"""

import sys
from pathlib import Path

# Ensure testing directory is accessible
TESTING_DIR = Path(__file__).resolve().parent.parent.parent / "testing"
if str(TESTING_DIR) not in sys.path:
    sys.path.insert(0, str(TESTING_DIR))

from testing.unit.test_ocr import OCRSubsystemTestSuite

__all__ = ["OCRSubsystemTestSuite"]
