import os
import subprocess
import tempfile
from pathlib import Path


class PDFConversionError(RuntimeError):
    pass


class LibreOfficePDFConverter:
    def __init__(self, executable: str | None = None, timeout: int = 120):
        self.executable = executable or os.getenv("LIBREOFFICE_BIN", "libreoffice")
        self.timeout = timeout

    def convert(self, docx_path: str | Path, output_dir: str | Path) -> Path:
        docx_path = Path(docx_path).resolve()
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        if not docx_path.exists():
            raise PDFConversionError(f"DOCX file does not exist: {docx_path}")

        with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile_dir:
            cmd = [
                self.executable,
                f"-env:UserInstallation=file://{profile_dir}",
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(docx_path),
            ]
            env = os.environ.copy()
            env.setdefault("HOME", "/tmp")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )

        expected_pdf = output_dir / f"{docx_path.stem}.pdf"
        if result.returncode != 0 or not expected_pdf.exists():
            details = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
            raise PDFConversionError(details or "LibreOffice failed to convert DOCX to PDF.")

        return expected_pdf
