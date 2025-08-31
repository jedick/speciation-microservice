import AqEquil
import tempfile
import json
import os
import pickle
import base64

def handler(event, context):
    
    try:
        # Parse the event payload to extract the CSV data
        if isinstance(event, str):
            # If event is a string, try to parse it as JSON
            payload = json.loads(event)
        else:
            # If event is already a dict, use it directly
            payload = event
        
        # Extract the CSV data from the payload
        csv_data = payload.get('input', '')

    except Exception as e:
        # Handle parsing errors gracefully
        return f"Error parsing input: {str(e)}"
    
    # Create temporary file for input
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as input_file:
        input_file.write(csv_data)
    
    try:
        # Initialize AqEquil
        # https://nbviewer.org/github/worm-portal/WORM-Library/blob/master/3-Aqueous-Speciation/1-Introduction-to-Aq-Speciation/2-Intro-to-Multi-Aq-Speciation.ipynb
        ae = AqEquil.AqEquil(db="wrm")

        # Change working directory to /tmp (writable on AWS Lambda - 512 MB size limit)
        os.chdir('/tmp')
        
        # Perform speciation calculation
        speciation = ae.speciate(
            input_filename=input_file.name,
            # Exclude metadata columns
            exclude=["Year", "Area"],
            # Don't create file, we'll read from memory
            report_filename=None,
            delete_generated_folders=True
        )
        
        # Clean up temporary input file
        os.unlink(input_file.name)
        
        # Process the output data
        #if hasattr(speciation, 'report'):
        #    # Convert speciation.report (a pandas DataFrame) to CSV string
        #    return speciation.report.to_csv(index = False)
        #else:
        #    return "Error: Could not retrieve speciation results"

        # Drop the batch_3o attribute (speciation results in R format) so our pickle doesn't depend on rpy2/R
        del speciation.batch_3o
        # Serialize the object using pickle
        pickled_data = pickle.dumps(speciation)
        # Encode the pickled data into Base64
        encoded_data = base64.b64encode(pickled_data).decode('utf-8')
        return encoded_data
        
    except Exception as e:
        # Clean up temporary file on error
        os.unlink(input_file.name)
        
        return f'Speciation calculation failed: {str(e)}'

