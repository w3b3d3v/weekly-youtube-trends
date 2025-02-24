from firebase_admin import initialize_app
from firebase_functions import https_fn, firestore_fn, scheduler_fn
from flask import jsonify
from scraper import main

# Initialize Firebase Admin
initialize_app()

@scheduler_fn.on_schedule(schedule="every monday 00:00")
def weekly_process_channels(event: scheduler_fn.ScheduledEvent) -> None:
    """Cloud Function that runs weekly to process all channels."""
    try:
        main()
        return jsonify({
            'status': 'success', 
            'message': 'Weekly channel processing completed successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@firestore_fn.on_document_created(document="channels/{channelId}")
def on_channel_created(event: firestore_fn.Event) -> None:
    """Cloud Function triggered when a new channel document is created."""
    try:
        main()
        return jsonify({
            'status': 'success', 
            'message': 'New channel processed successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500