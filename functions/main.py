from firebase_admin import initialize_app
from firebase_functions import https_fn, firestore_fn, scheduler_fn
from flask import jsonify, request
from scraper import main
from firebase_service import FirebaseService
from claude_service import ClaudeService

# Initialize services
firebase_service = FirebaseService()
claude_service = ClaudeService(firebase_service)

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

@https_fn.on_request(timeout_sec=540)
def generate_custom_summary(req: https_fn.Request) -> None:
    """Generate a custom summary for a video using a provided prompt."""
    try:
        # Get request data
        data = req.get_json()
        video_id = data.get('video_id')
        custom_prompt = data.get('prompt')

        # Validate input
        if not video_id or not custom_prompt:
            return jsonify({
                'status': 'error',
                'message': 'Both video_id and prompt are required'
            }), 400

        # Get video data from Firebase
        video_data = firebase_service.get_video(video_id)
        if not video_data:
            return jsonify({
                'status': 'error',
                'message': 'Video not found'
            }), 404

        # Check if video has transcript
        if not video_data.get('transcript'):
            return jsonify({
                'status': 'error',
                'message': 'Video has no transcript available'
            }), 400

        # Generate summary using custom prompt
        summary_result = claude_service.summarize_transcript(
            video_data['transcript'],
            video_data['title'],
            custom_prompt
        )

        return jsonify({
            'status': 'success',
            'video_id': video_id,
            'title': video_data['title'],
            'summary': summary_result['summary'],
            'has_summary': summary_result['has_summary']
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# @scheduler_fn.on_schedule(schedule="every day 00:00")
# def daily_process_channels(event: scheduler_fn.ScheduledEvent) -> None:
#     """Cloud Function that runs weekly to process all channels."""
#     try:
#         main()
#         return jsonify({
#             'status': 'success', 
#             'message': 'Daily channel processing completed successfully'
#         })
#     except Exception as e:
#         return jsonify({
#             'status': 'error', 
#             'message': str(e)
#         }), 500