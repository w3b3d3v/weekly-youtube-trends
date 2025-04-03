from firebase_admin import initialize_app
from firebase_functions import https_fn, firestore_fn, scheduler_fn
from flask import jsonify
from scraper import main

@https_fn.on_request()
def run_full_process(req: https_fn.Request) -> None:
    """Cloud Function to manually trigger the full processing flow."""
    try:
        main()
        return jsonify({
            'status': 'success',
            'message': 'Full process completed successfully!'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@scheduler_fn.on_schedule(schedule="every day 00:00")
def daily_process_channels(event: scheduler_fn.ScheduledEvent) -> None:
    """Cloud Function that runs weekly to process all channels."""
    try:
        main()
        return jsonify({
            'status': 'success', 
            'message': 'Daily channel processing completed successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500