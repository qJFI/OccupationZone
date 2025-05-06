from automation.linkedin_applier import apply_to_linkedin_job
from automation.wuzzuf_applier import apply_to_wuzzuf_job
from automation.freelancer_applier import apply_to_freelancer_job

def apply_to_job(job, resume_path, labels, credentials):
    source = job['source'].lower()
    if source == 'linkedin':
        return apply_to_linkedin_job(job['link'], resume_path, labels, credentials['linkedin_email'], credentials['linkedin_password'])
    elif source == 'wuzzuf':
        return apply_to_wuzzuf_job(job['link'], resume_path, labels, credentials['wuzzuf_email'], credentials['wuzzuf_password'])
    elif source == 'freelancer':
        return apply_to_freelancer_job(job['link'], resume_path, labels, credentials['freelancer_email'], credentials['freelancer_password'])
    else:
        return False, f"Automation for {job['source']} not implemented yet." 