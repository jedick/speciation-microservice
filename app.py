import AqEquil
import tempfile
import json
import os
import pickle
import base64

def handler(event, context):
    
    try:
        if isinstance(event, dict):
            # If event is a dict, we're on AWS Lambda
            # Parse the body of the request from the 'body' field
            # https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html
            # TODO: why is a double json.loads needed here?
            body = json.loads(json.loads(event['body']))
        else:
            # For local testing, just parse the JSON event string
            body = json.loads(event)

        # Extract the CSV data from the 'input' field
        csv_data = body['input']

    except Exception as e:
        # Handle parsing errors gracefully
        return f"Error parsing input: {str(e)}\nBody: {body}"
    
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
        if hasattr(speciation, 'report'):
            # Convert speciation.report (a pandas DataFrame) to CSV string
            report_csv = speciation.report.to_csv(index = False)
            #return report_csv

            # Create a scatterplot of pH and Temperature
            # Use plot_out to return a plotly figure object
            plot_output = speciation.scatterplot('pH', 'Temperature', plot_out=True)
            # Serialize the object using pickle
            plot_pickled = pickle.dumps(plot_output)
            # Encode the pickled data into Base64, then convert it to a string
            plot_encoded = base64.b64encode(plot_pickled).decode('utf-8')

            ## TODO: return both report_csv and plot_output
            return report_csv, plot_encoded
        else:
            return "Error: Could not retrieve speciation results"

    except Exception as e:
        try:
            # Clean up temporary file on error
            os.unlink(input_file.name)
        except:
            pass
        
        return f'Speciation calculation failed: {str(e)}'

