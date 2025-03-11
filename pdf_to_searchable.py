import os
import sys
import time
import json
import argparse
import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

def create_document_intelligence_client(endpoint, key):
    """Create Document Intelligence client with Azure credentials."""
    try:
        credential = AzureKeyCredential(key)
        document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=credential)
        return document_intelligence_client
    except Exception as e:
        print(f"Error creating Document Intelligence client: {str(e)}")
        sys.exit(1)

def convert_to_searchable_pdf_rest(endpoint, key, input_file_path, output_file_path):
    """Convert a scanned PDF to a searchable PDF using Document Intelligence REST API."""
    print(f"REST API - Starting conversion of: {input_file_path}")
    
    # Ensure endpoint doesn't end with a slash
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
    
    # Read the PDF file
    with open(input_file_path, "rb") as f:
        pdf_content = f.read()
    
    print(f"REST API - File read, size: {len(pdf_content)} bytes")
    
    # Set up headers with authentication
    headers = {
        "Content-Type": "application/pdf",
        "Ocp-Apim-Subscription-Key": key,
    }
    
    # Construct the URL for analyze operation with PDF output
    analyze_url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read:analyze?api-version=2024-11-30&output=pdf"
    
    print(f"REST API - Sending request to: {analyze_url}")
    
    # Submit the analyze request
    try:
        response = requests.post(analyze_url, headers=headers, data=pdf_content)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Get the operation ID from the response header
        if 'Operation-Location' in response.headers:
            operation_location = response.headers['Operation-Location']
            print(f"REST API - Operation location: {operation_location}")
            
            # Extract just the operation ID without any query parameters
            if '?' in operation_location:
                operation_id = operation_location.split('?')[0].split('/')[-1]
            else:
                operation_id = operation_location.split('/')[-1]
                
            print(f"REST API - Extracted operation ID: {operation_id}")
        else:
            print(f"REST API - Error: No Operation-Location header in response")
            print(f"REST API - Response headers: {response.headers}")
            print(f"REST API - Response content: {response.content}")
            return None
    except Exception as e:
        print(f"REST API - Error submitting document: {str(e)}")
        return None
    
    # Poll for completion
    status_url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read/analyzeResults/{operation_id}?api-version=2024-11-30"
    
    print(f"REST API - Polling for completion at: {status_url}")
    
    # Use a timeout to prevent infinite waiting
    max_retries = 60
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            status_response = requests.get(status_url, headers={"Ocp-Apim-Subscription-Key": key})
            status_response.raise_for_status()
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            print(f"REST API - Current status: {status}")
            
            if status == "succeeded":
                print("REST API - Analysis completed successfully")
                break
            elif status == "failed":
                print(f"REST API - Analysis failed: {json.dumps(status_data)}")
                return None
            
            # Wait before polling again
            print("REST API - Waiting 5 seconds before checking status again...")
            time.sleep(5)
            retry_count += 1
        except Exception as e:
            print(f"REST API - Error checking status: {str(e)}")
            retry_count += 1
            time.sleep(5)
    
    if retry_count >= max_retries:
        print("REST API - Operation timed out")
        return None
    
    # Download the searchable PDF
    pdf_url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read/analyzeResults/{operation_id}/pdf?api-version=2024-11-30"
    
    print(f"REST API - Downloading searchable PDF from: {pdf_url}")
    
    try:
        pdf_response = requests.get(pdf_url, headers={"Ocp-Apim-Subscription-Key": key})
        pdf_response.raise_for_status()
        
        # Write the PDF to file
        with open(output_file_path, "wb") as output_file:
            output_file.write(pdf_response.content)
        
        print(f"REST API - Searchable PDF created and saved to: {output_file_path}")
        return output_file_path
    except Exception as e:
        print(f"REST API - Error downloading PDF: {str(e)}")
        return None
    

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
    
    # Determine if input is a single file or directory
    if os.path.isfile(args.input):
        # Process a single file
        if args.input.lower().endswith('.pdf'):
            output_path = args.output if args.output else os.path.dirname(args.input)
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            output_filename = os.path.join(output_path, f"searchable_{os.path.basename(args.input)}")
            # Use the REST API version instead of the SDK
            convert_to_searchable_pdf_rest(args.endpoint, args.key, args.input, output_filename)
        else:
            print(f"Error: {args.input} is not a PDF file")
    
    elif os.path.isdir(args.input):
        # Process all PDFs in a directory
        output_path = args.output if args.output else args.input
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        pdf_files = [f for f in os.listdir(args.input) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print(f"No PDF files found in {args.input}")
            return
        
        for pdf_file in pdf_files:
            input_path = os.path.join(args.input, pdf_file)
            output_filename = os.path.join(output_path, f"searchable_{pdf_file}")
            # Use the REST API version instead of the SDK
            convert_to_searchable_pdf_rest(args.endpoint, args.key, input_path, output_filename)
    
    else:
        print(f"Error: {args.input} is not a valid file or directory")

if __name__ == "__main__":
    main()