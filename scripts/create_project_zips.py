"""
=============================================================================
StudyAI — Multi-Bundle Packaging & Distribution Generator
=============================================================================
Creates clean, modular, production-ready ZIP distribution archives:
1. studyai_frontend.zip (React 19 + Vite + Tailwind + Lucide + KaTeX + Mermaid)
2. studyai_backend.zip (Django 5 + REST APIs + SQLite DB + Processing Engines)
3. studyai_testing.zip (Unit, Acceptance, AI Synthesis Benchmarks, Test Harness)
4. studyai_docs.zip (Architecture audits, subject engine specs, troubleshooting)
5. studyai_docker_and_scripts.zip (Dockerfiles, compose, cross-platform launchers)
6. studyai_sample_materials_and_media.zip (Uploaded PDF study materials & dataset)
7. studyai_complete_project.zip (All-in-one complete master bundle, zero-bloat)
=============================================================================
"""

import os
import sys
import zipfile
import shutil
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "project_zips"

# Global exclusions to ensure lean, clean archives without bloating
GLOBAL_EXCLUDES_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".oxlint_cache",
    "project_zips",
    ".agents"
}

GLOBAL_EXCLUDES_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".DS_Store",
    ".log"
}


def should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in GLOBAL_EXCLUDES_DIRS:
            return True
    if path.suffix.lower() in GLOBAL_EXCLUDES_EXTS:
        return True
    return False


def create_zip_archive(zip_filename: str, root_prefix: str, file_mappings: list):
    """
    Creates a ZIP archive with specified file mappings.
    file_mappings: list of tuples (source_path, archive_internal_path)
    """
    zip_path = OUTPUT_DIR / zip_filename
    print(f"\n[PACKAGING] Creating {zip_filename}...")
    start_time = time.time()
    file_count = 0
    total_uncompressed = 0

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc_name in file_mappings:
            src_path = Path(src)
            if not src_path.exists():
                continue

            if src_path.is_file():
                if not should_exclude(src_path):
                    target_arc = f"{root_prefix}/{arc_name}" if root_prefix else arc_name
                    zf.write(src_path, target_arc)
                    file_count += 1
                    total_uncompressed += src_path.stat().st_size
            elif src_path.is_dir():
                for root, dirs, files in os.walk(src_path):
                    dirs[:] = [d for d in dirs if d not in GLOBAL_EXCLUDES_DIRS]
                    for f in files:
                        fp = Path(root) / f
                        if not should_exclude(fp):
                            rel = fp.relative_to(src_path)
                            target_arc = f"{root_prefix}/{arc_name}/{rel.as_posix()}" if arc_name else f"{root_prefix}/{rel.as_posix()}"
                            target_arc = target_arc.replace("//", "/")
                            zf.write(fp, target_arc)
                            file_count += 1
                            total_uncompressed += fp.stat().st_size

    elapsed = round(time.time() - start_time, 2)
    compressed_size = zip_path.stat().st_size
    print(f" -> Files: {file_count} | Uncompressed: {round(total_uncompressed / (1024*1024), 2)} MB | ZIP Size: {round(compressed_size / (1024*1024), 2)} MB | Time: {elapsed}s")
    return {
        "filename": zip_filename,
        "path": str(zip_path),
        "files_count": file_count,
        "size_bytes": compressed_size,
        "size_mb": round(compressed_size / (1024 * 1024), 2),
        "uncompressed_mb": round(total_uncompressed / (1024 * 1024), 2)
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    # -------------------------------------------------------------------------
    # 1. FRONTEND PACKAGE (studyai_frontend.zip)
    # -------------------------------------------------------------------------
    frontend_files = [
        (BASE_DIR / "frontend" / "src", "src"),
        (BASE_DIR / "frontend" / "public", "public"),
        (BASE_DIR / "frontend" / "dist", "dist"),
        (BASE_DIR / "frontend" / "package.json", "package.json"),
        (BASE_DIR / "frontend" / "package-lock.json", "package-lock.json"),
        (BASE_DIR / "frontend" / "vite.config.js", "vite.config.js"),
        (BASE_DIR / "frontend" / "index.html", "index.html"),
        (BASE_DIR / "frontend" / "nginx.conf", "nginx.conf"),
        (BASE_DIR / "frontend" / "eslint.config.js", "eslint.config.js"),
        (BASE_DIR / "frontend" / ".oxlintrc.json", ".oxlintrc.json"),
        (BASE_DIR / "frontend" / "README.md", "README.md"),
    ]
    res_fe = create_zip_archive("studyai_frontend.zip", "studyai-frontend", frontend_files)
    results.append(res_fe)

    # -------------------------------------------------------------------------
    # 2. BACKEND PACKAGE (studyai_backend.zip)
    # -------------------------------------------------------------------------
    backend_files = [
        (BASE_DIR / "backend" / "api", "api"),
        (BASE_DIR / "backend" / "studyai_backend", "studyai_backend"),
        (BASE_DIR / "backend" / "staticfiles", "staticfiles"),
        (BASE_DIR / "backend" / "manage.py", "manage.py"),
        (BASE_DIR / "backend" / "requirements.txt", "requirements.txt"),
        (BASE_DIR / "backend" / "requirements.lock", "requirements.lock"),
        (BASE_DIR / "backend" / "db.sqlite3", "db.sqlite3"),
        (BASE_DIR / "backend" / "README.md", "README.md"),
        (BASE_DIR / ".env.example", ".env.example"),
    ]
    res_be = create_zip_archive("studyai_backend.zip", "studyai-backend", backend_files)
    results.append(res_be)

    # -------------------------------------------------------------------------
    # 3. TESTING PACKAGE (studyai_testing.zip)
    # -------------------------------------------------------------------------
    testing_files = [
        (BASE_DIR / "testing" / "acceptance", "acceptance"),
        (BASE_DIR / "testing" / "ai_evaluation", "ai_evaluation"),
        (BASE_DIR / "testing" / "unit", "unit"),
        (BASE_DIR / "testing" / "reports", "reports"),
        (BASE_DIR / "testing" / "run_tests.py", "run_tests.py"),
        (BASE_DIR / "testing" / "README.md", "README.md"),
    ]
    res_test = create_zip_archive("studyai_testing.zip", "studyai-testing", testing_files)
    results.append(res_test)

    # -------------------------------------------------------------------------
    # 4. DOCUMENTATION PACKAGE (studyai_docs.zip)
    # -------------------------------------------------------------------------
    docs_files = [
        (BASE_DIR / "docs" / "reports", "reports"),
        (BASE_DIR / "docs" / "TROUBLESHOOTING.md", "TROUBLESHOOTING.md"),
        (BASE_DIR / "docs" / "TROUBLESHOOTING_OCR.md", "TROUBLESHOOTING_OCR.md"),
        (BASE_DIR / "README.md", "README.md"),
    ]
    res_docs = create_zip_archive("studyai_docs.zip", "studyai-docs", docs_files)
    results.append(res_docs)

    # -------------------------------------------------------------------------
    # 5. DOCKER & RUN SCRIPTS (studyai_docker_and_scripts.zip)
    # -------------------------------------------------------------------------
    deploy_files = [
        (BASE_DIR / "docker-compose.yml", "docker-compose.yml"),
        (BASE_DIR / "Dockerfile.backend", "Dockerfile.backend"),
        (BASE_DIR / "Dockerfile.frontend", "Dockerfile.frontend"),
        (BASE_DIR / "start_studyai.bat", "start_studyai.bat"),
        (BASE_DIR / "start_studyai.sh", "start_studyai.sh"),
        (BASE_DIR / "setup_studyai.bat", "setup_studyai.bat"),
        (BASE_DIR / "setup_studyai.sh", "setup_studyai.sh"),
        (BASE_DIR / "start_all.js", "start_all.js"),
        (BASE_DIR / "package.json", "package.json"),
        (BASE_DIR / "package-lock.json", "package-lock.json"),
        (BASE_DIR / ".env.example", ".env.example"),
        (BASE_DIR / ".nvmrc", ".nvmrc"),
        (BASE_DIR / ".python-version", ".python-version"),
    ]
    res_deploy = create_zip_archive("studyai_docker_and_scripts.zip", "studyai-deployment", deploy_files)
    results.append(res_deploy)

    # -------------------------------------------------------------------------
    # 6. SAMPLE MATERIALS & MEDIA (studyai_sample_materials_and_media.zip)
    # -------------------------------------------------------------------------
    media_files = [
        (BASE_DIR / "backend" / "media", "media"),
    ]
    res_media = create_zip_archive("studyai_sample_materials_and_media.zip", "studyai-media", media_files)
    results.append(res_media)

    # -------------------------------------------------------------------------
    # 7. COMPLETE PROJECT ALL-IN-ONE (studyai_complete_project.zip)
    # -------------------------------------------------------------------------
    complete_files = [
        # Root Files
        (BASE_DIR / "package.json", "package.json"),
        (BASE_DIR / "package-lock.json", "package-lock.json"),
        (BASE_DIR / "start_all.js", "start_all.js"),
        (BASE_DIR / "start_studyai.bat", "start_studyai.bat"),
        (BASE_DIR / "start_studyai.sh", "start_studyai.sh"),
        (BASE_DIR / "setup_studyai.bat", "setup_studyai.bat"),
        (BASE_DIR / "setup_studyai.sh", "setup_studyai.sh"),
        (BASE_DIR / "docker-compose.yml", "docker-compose.yml"),
        (BASE_DIR / "Dockerfile.backend", "Dockerfile.backend"),
        (BASE_DIR / "Dockerfile.frontend", "Dockerfile.frontend"),
        (BASE_DIR / "README.md", "README.md"),
        (BASE_DIR / ".env.example", ".env.example"),
        (BASE_DIR / ".gitignore", ".gitignore"),
        (BASE_DIR / ".nvmrc", ".nvmrc"),
        (BASE_DIR / ".python-version", ".python-version"),
        # Subdirectories
        (BASE_DIR / "frontend" / "src", "frontend/src"),
        (BASE_DIR / "frontend" / "public", "frontend/public"),
        (BASE_DIR / "frontend" / "dist", "frontend/dist"),
        (BASE_DIR / "frontend" / "package.json", "frontend/package.json"),
        (BASE_DIR / "frontend" / "package-lock.json", "frontend/package-lock.json"),
        (BASE_DIR / "frontend" / "vite.config.js", "frontend/vite.config.js"),
        (BASE_DIR / "frontend" / "index.html", "frontend/index.html"),
        (BASE_DIR / "frontend" / "nginx.conf", "frontend/nginx.conf"),
        (BASE_DIR / "frontend" / "eslint.config.js", "frontend/eslint.config.js"),
        (BASE_DIR / "frontend" / ".oxlintrc.json", "frontend/.oxlintrc.json"),
        (BASE_DIR / "frontend" / "README.md", "frontend/README.md"),
        (BASE_DIR / "backend" / "api", "backend/api"),
        (BASE_DIR / "backend" / "studyai_backend", "backend/studyai_backend"),
        (BASE_DIR / "backend" / "staticfiles", "backend/staticfiles"),
        (BASE_DIR / "backend" / "manage.py", "backend/manage.py"),
        (BASE_DIR / "backend" / "requirements.txt", "backend/requirements.txt"),
        (BASE_DIR / "backend" / "requirements.lock", "backend/requirements.lock"),
        (BASE_DIR / "backend" / "db.sqlite3", "backend/db.sqlite3"),
        (BASE_DIR / "backend" / "README.md", "backend/README.md"),
        (BASE_DIR / "testing", "testing"),
        (BASE_DIR / "docs", "docs"),
    ]
    res_complete = create_zip_archive("studyai_complete_project.zip", "studyai-master", complete_files)
    results.append(res_complete)

    print("\n" + "=" * 80)
    print("ALL DISTRIBUTION PACKAGES GENERATED SUCCESSFULLY!")
    print("=" * 80)
    for r in results:
        print(f"  • {r['filename']:<35} | Size: {r['size_mb']:>6.2f} MB ({r['files_count']} files)")
    print("=" * 80)


if __name__ == "__main__":
    main()

