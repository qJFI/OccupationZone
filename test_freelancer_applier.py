import sys
import os
from automation.freelancer_applier import apply_to_freelancer_job
import argparse

def test_freelancer_applier(email, password, job_url, resume_path, debug_mode=False):
    # Sample labels (not used much since we have fixed description)
    labels = {
        'salary_expectations': '50',  # Hourly rate in dollars
        'availability': '1',          # Delivery time in days/weeks
        'overview': 'Not used'        # Not used as we have fixed description
    }
    
    print(f"Testing Freelancer applier with:")
    print(f"Email: {email}")
    print(f"Job URL: {job_url}")
    print(f"Resume path: {resume_path}")
    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
    
    # Attempt to apply
    success, message = apply_to_freelancer_job(job_url, resume_path, labels, email, password, debug_mode)
    
    # Print result
    if success:
        print("✓ SUCCESS: Application submitted successfully!")
        print(f"Message: {message}")
    else:
        print("✗ FAILED: Could not submit application")
        print(f"Error: {message}")
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test the Freelancer job application automation')
    parser.add_argument('--email', required=True, help='Your Freelancer email')
    parser.add_argument('--password', required=True, help='Your Freelancer password')
    parser.add_argument('--job_url', required=True, help='URL of the Freelancer job to bid on')
    parser.add_argument('--resume', default='resumes/default_resume.pdf', help='Path to your resume file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with manual intervention')
    
    args = parser.parse_args()
    
    # Ensure the resume file exists
    if not os.path.exists(args.resume):
        print(f"Error: Resume file not found at {args.resume}")
        sys.exit(1)
    
    # Run the test
    success = test_freelancer_applier(args.email, args.password, args.job_url, args.resume, args.debug)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 