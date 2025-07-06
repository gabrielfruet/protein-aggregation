import requests
import time
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)

AGGRESCAN_SUBMIT_URL = "https://biocomp.chem.uw.edu.pl/A3D2/RESTful/submit/userinput/"
AGGRESCAN_RESULT_URL_TEMPLATE = "https://biocomp.chem.uw.edu.pl/A3D2/RESTful/job/{job_id}/"

def get_aggregation_score_from_server(pdb_content: str) -> Optional[float]:
    """
    Submits a PDB file to the Aggrescan3D RESTful API and retrieves the score.
    This function contains the final, working logic from our tests.
    """
    logger.info("Submitting PDB to Aggrescan3D RESTful API...")
    options = {'distance': 10, 'hide': True}
    files = {
        'inputfile': ('protein.pdb', pdb_content, 'text/plain'),
        'json': (None, json.dumps(options), 'application/json')
    }

    try:
        response = requests.post(AGGRESCAN_SUBMIT_URL, files=files, timeout=30)
        response.raise_for_status()
        job_id = response.json().get("jobid")

        if not job_id:
            logger.error("API submission did not return a job ID.")
            return None

        logger.info(f"Job submitted with ID: {job_id}")
        results_url = AGGRESCAN_RESULT_URL_TEMPLATE.format(job_id=job_id)

        for i in range(24):  
            time.sleep(5)
            status_response = requests.get(results_url, timeout=30)
            try:
                status_data = status_response.json()
                job_status = status_data.get("status")
            except json.JSONDecodeError:
                logger.warning("Waiting for job (server returned non-JSON)...")
                continue

            if job_status not in ["running", "queue", "pending"]:
                logger.info(f"Job is no longer running. Final status: '{job_status}'.")
                break
        
        final_response = requests.get(results_url, timeout=30)
        final_data = final_response.json()

        if final_data.get("status") == "done":
            a3d_data = final_data.get("A3Dscore")
            if a3d_data:
                avg_score = a3d_data.get("avg")
                if avg_score is not None:
                    logger.info("Successfully retrieved Aggrescan score.")
                    return float(avg_score)

        logger.error(f"Could not retrieve score after job completion. Final data: {final_data}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the API call: {e}")
        return None