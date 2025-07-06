
import asyncio
import aiohttp
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

SUBMIT_URL = "https://biocomp.chem.uw.edu.pl/A3D2/RESTful/submit/userinput/"
RESULT_URL_TEMPLATE = "https://biocomp.chem.uw.edu.pl/A3D2/RESTful/job/{job_id}/"
MAX_CONCURRENT_TASKS = 8


async def _get_single_agg_score(semaphore: asyncio.Semaphore, session: aiohttp.ClientSession, pdb_content: str) -> Optional[float]:
    """The core async function to get a single score, with a retry mechanism."""
    if not pdb_content:
        return None

    async with semaphore:
        try:
            options = {'distance': 10, 'hide': True}
            form_data = aiohttp.FormData()
            form_data.add_field('inputfile', pdb_content, filename='protein.pdb', content_type='text/plain')
            form_data.add_field('json', json.dumps(options), content_type='application/json')
            
            async with session.post(SUBMIT_URL, data=form_data, timeout=30) as response:
                response.raise_for_status()
                job_id = (await response.json()).get("jobid")

            if not job_id:
                logger.error("Submission failed, no job ID returned.")
                return None

            results_url = RESULT_URL_TEMPLATE.format(job_id=job_id)
            for _ in range(24): 
                await asyncio.sleep(5)
                
                for retry_attempt in range(3): 
                    try:
                        async with session.get(results_url, timeout=30) as result_response:
                            result_data = await result_response.json()
                            job_status = result_data.get("status")
                            
                            if job_status == "done":
                                a3d_data = result_data.get("A3Dscore", {})
                                avg_score = a3d_data.get("avg")
                                if avg_score is not None:
                                    return float(avg_score)
                            
                            break 
                    
                    except (aiohttp.client_exceptions.ServerDisconnectedError, asyncio.TimeoutError) as e:
                        logger.warning(f"Connection error for job {job_id} (retry {retry_attempt + 1}/3): {e}. Retrying...")
                        await asyncio.sleep(2)
                else: 
                    logger.error(f"Job {job_id} failed after multiple retries. Giving up.")
                    return None

            logger.error(f"Polling timed out for job {job_id}.")
            return None

        except Exception as e:
            logger.error(f"An unexpected error occurred in the aggregation task: {e}", exc_info=True)
            return None

async def get_aggregation_scores_in_parallel(pdbs: List[str]) -> List[Optional[float]]:
    """
    The main public function that runs all Aggrescan requests concurrently.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    async with aiohttp.ClientSession() as session:
        tasks = [_get_single_agg_score(semaphore, session, pdb) for pdb in pdbs]
        agg_results = await asyncio.gather(*tasks)
        return agg_results