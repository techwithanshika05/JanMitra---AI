from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
import os
import traceback

# Load environment variables
load_dotenv()

# Read API key
api_key = os.getenv("SARVAM_API_KEY")

if not api_key:
    raise ValueError("SARVAM_API_KEY not found in .env file")

print("✓ API Key Loaded")

# Locate PDF relative to this script
pdf_path = Path(__file__).resolve().parent / "sample.pdf"

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")

print(f"✓ PDF Found: {pdf_path}")

try:
    client = SarvamAI(
        api_subscription_key=api_key
    )

    print("✓ Client Created")

    job = client.document_intelligence.create_job(
        language="en-IN",
        output_format="md"
    )

    print("✓ Job Created")

    job.upload_file(str(pdf_path))

    print("✓ File Uploaded")

    job.start()

    print("✓ Job Started")

    status = job.wait_until_complete()

    print("✓ Job Status:", status)

    output_zip = Path(__file__).resolve().parent / "output.zip"

    job.download_output(str(output_zip))

    print(f"✓ Output Downloaded: {output_zip}")

except Exception:
    print("\n❌ ERROR OCCURRED\n")
    traceback.print_exc()