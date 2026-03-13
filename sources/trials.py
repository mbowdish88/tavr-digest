from __future__ import annotations

import logging
from datetime import datetime, timedelta

import requests

import config

logger = logging.getLogger(__name__)


def fetch_trial_updates(days: int = None) -> list[dict]:
    """Fetch recently updated TAVR clinical trials from ClinicalTrials.gov v2 API."""
    days = days or config.LOOKBACK_DAYS

    # Fetch the most recently updated trials, then filter by date in Python
    params = {
        "query.cond": config.CLINICALTRIALS_QUERY,
        "sort": "LastUpdatePostDate",
        "pageSize": 50,
    }

    try:
        resp = requests.get(config.CLINICALTRIALS_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"ClinicalTrials.gov API failed: {e}")
        return []
    except ValueError as e:
        logger.error(f"ClinicalTrials.gov JSON parse failed: {e}")
        return []

    studies = data.get("studies", [])
    # Use a wider window for trials (7 days minimum) since updates can lag
    cutoff_date = (datetime.now() - timedelta(days=max(days + 1, 7))).strftime("%Y-%m-%d")
    trials = []

    for study in studies:
        try:
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            sponsor = proto.get("sponsorCollaboratorsModule", {})
            arms = proto.get("armsInterventionsModule", {})

            nct_id = ident.get("nctId", "")
            title = ident.get("briefTitle", "No title")
            overall_status = status_mod.get("overallStatus", "Unknown")
            phase_list = (design or {}).get("phases", [])
            phase = ", ".join(phase_list) if phase_list else "N/A"

            enrollment_info = (design or {}).get("enrollmentInfo", {})
            enrollment = enrollment_info.get("count", "N/A") if enrollment_info else "N/A"

            lead_sponsor = (sponsor or {}).get("leadSponsor", {}).get("name", "Unknown")

            last_update = status_mod.get("lastUpdatePostDateStruct", {}).get("date", "")
            start_date = status_mod.get("startDateStruct", {}).get("date", "")
            completion_date = (status_mod.get("completionDateStruct") or {}).get("date", "")

            # Filter by date
            if last_update and last_update < cutoff_date:
                continue

            # Interventions
            interventions = (arms or {}).get("interventions", [])
            intervention_names = [i.get("name", "") for i in interventions if i.get("name")]

            trials.append({
                "nct_id": nct_id,
                "title": title,
                "status": overall_status,
                "phase": phase,
                "enrollment": enrollment,
                "sponsor": lead_sponsor,
                "last_update": last_update,
                "start_date": start_date,
                "completion_date": completion_date,
                "interventions": ", ".join(intervention_names[:3]),
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            })

            if len(trials) >= 20:
                break

        except Exception as e:
            logger.warning(f"Failed to parse trial: {e}")

    logger.info(f"ClinicalTrials.gov: retrieved {len(trials)} recently updated trials")
    return trials
