import os
import sys
import time
import json
import argparse
import requests
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

# Constants
API_VERSION = "2024-11-30"
MAX_POLLING_RETRIES = 60
POLLING_INTERVAL = 5  # seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_document_intelligence_client(endpoint, key):
    """Create Document Intelligence client with Azure credentials."""
    try:
        credential = AzureKeyCredential(key)
        document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=credential)
        return document_intelligence_client
    except Exception as e:
        logger.error(f"Error creating Document Intelligence client: {str(e)}")
        sys.exit(1)


def submit_document_for_analysis(endpoint, key, pdf_content):
    """Submit a document for analysis and return the operation ID."""
    # Ensure endpoint doesn't end with a slash
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]

    headers = {
        "Content-Type": "application/pdf",
        "Ocp-Apim-Subscription-Key": key,
    }

    analyze_url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read:analyze?api-version={API_VERSION}&output=pdf"

    logger.info(f"Sending request to: {analyze_url}")

    try:
        response = requests.post(analyze_url, headers=headers, data=pdf_content)
        response.raise_for_status()

        if 'Operation-Location' not in response.headers:
            logger.error(f"No Operation-Location header in response: {response.headers}")
            return None

        operation_location = response.headers['Operation-Location']
        operation_id = operation_location.split('/')[-1].split('?')[0]
        logger.info(f"Received operation ID: {operation_id}")
        return operation_id
    except Exception as e:
        logger.error(f"Error submitting document: {e}")
        return None


def poll_for_completion(endpoint, key, operation_id):
    """Poll until the operation completes and return True if successful."""
    status_url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read/analyzeResults/{operation_id}?api-version={API_VERSION}"
    logger.info(f"Polling for completion at: {status_url}")

    for attempt in range(MAX_POLLING_RETRIES):
        try:
            headers = {"Ocp-Apim-Subscription-Key": key}
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()

            status_data = status_response.json()
            status = status_data.get("status")

            logger.info(f"Current status: {status}")

            if status == "succeeded":
                logger.info("Analysis completed successfully")
                return True
            elif status == "failed":
                logger.error(f"Analysis failed: {json.dumps(status_data)}")
                return False

            logger.info(f"Waiting {POLLING_INTERVAL} seconds before checking status again...")
            time.sleep(POLLING_INTERVAL)
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            time.sleep(POLLING_INTERVAL)
    
    logger.error("Operation timed out")
    return False


def download_searchable_pdf(endpoint, key, operation_id, output_file_path):
    """Download the searchable PDF and save it to the specified path."""
    pdf_url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read/analyzeResults/{operation_id}/pdf?api-version={API_VERSION}"
    logger.info(f"Downloading searchable PDF from: {pdf_url}")

    try:
        headers = {"Ocp-Apim-Subscription-Key": key}
        pdf_response = requests.get(pdf_url, headers=headers)
        pdf_response.raise_for_status()

        with open(output_file_path, "wb") as output_file:
            output_file.write(pdf_response.content)

        logger.info(f"Searchable PDF saved to: {output_file_path}")
        return output_file_path
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return None


def convert_to_searchable_pdf_rest(endpoint, key, input_file_path, output_file_path):
    """Convert a scanned PDF to a searchable PDF using Document Intelligence REST API."""
    logger.info(f"Starting conversion of: {input_file_path}")

    # Read the PDF file
    try:
        with open(input_file_path, "rb") as f:
            pdf_content = f.read()
        logger.info(f"File read, size: {len(pdf_content)} bytes")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        return None

    # Process in steps
    operation_id = submit_document_for_analysis(endpoint, key, pdf_content)
    if not operation_id:
        return None

    success = poll_for_completion(endpoint, key, operation_id)
    if not success:
        return None

    return download_searchable_pdf(endpoint, key, operation_id, output_file_path)


def process_file(endpoint, key, input_path, output_path):
    """Process a single PDF file."""
    if not input_path.lower().endswith('.pdf'):
        logger.error(f"Not a PDF file: {input_path}")
        return False

    output_filename = os.path.join(output_path, f"searchable_{os.path.basename(input_path)}")
    result = convert_to_searchable_pdf_rest(endpoint, key, input_path, output_filename)
    return result is not None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert scanned PDFs to searchable PDFs using Azure Document Intelligence')
    parser.add_argument('--input', '-i', required=True, help='Input PDF file path or directory containing PDFs')
    parser.add_argument('--output', '-o', help='Output directory for searchable PDFs (defaults to same as input)')
    parser.add_argument('--endpoint', '-e', required=True, help='Azure Document Intelligence endpoint')
    parser.add_argument('--key', '-k', required=True, help='Azure Document Intelligence key')
    return parser.parse_args()


def main():
    """Main program execution."""
    args = parse_arguments()

    # Ensure output directory exists
    output_path = args.output or (
        os.path.dirname(args.input) if os.path.isfile(args.input) else args.input
    )
    os.makedirs(output_path, exist_ok=True)

    if os.path.isfile(args.input):
        # Process single file
        process_file(args.endpoint, args.key, args.input, output_path)
    elif os.path.isdir(args.input):
        # Process all PDFs in a directory
        pdf_files = [f for f in os.listdir(args.input) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logger.warning(f"No PDF files found in {args.input}")
            return

        success_count = 0
        for pdf_file in pdf_files:
            input_path = os.path.join(args.input, pdf_file)
            if process_file(args.endpoint, args.key, input_path, output_path):
                success_count += 1

        logger.info(f"Processed {success_count} of {len(pdf_files)} PDF files successfully")
    else:
        logger.error(f"Error: {args.input} is not a valid file or directory")


if __name__ == "__main__":
    main()