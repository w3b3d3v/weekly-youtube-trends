import argparse
from firebase_service import FirebaseService

def add_channel_command():
    """
    CLI command to add a new YouTube channel.
    Prompts user for channel name and URL.
    """
    print("\n=== Add New YouTube Channel ===")
    
    # Get user input
    channel_name = input("Enter channel name: ").strip()
    channel_url = input("Enter channel URL: ").strip()
    
    # Validate inputs
    if not channel_name or not channel_url:
        print("Error: Channel name and URL cannot be empty")
        return
    
    try:
        # Initialize Firebase and add channel
        firebase = FirebaseService()
        firebase.add_channel(channel_name, channel_url)
        print(f"\nSuccess! Channel '{channel_name}' added with PENDING status")
    except Exception as e:
        print(f"Error adding channel: {str(e)}")

def handle_cli_commands():
    """Handle CLI commands and arguments"""
    parser = argparse.ArgumentParser(description='YouTube Channel Manager')
    parser.add_argument('--action', type=str, help='Action to perform (add_channel)')
    
    args = parser.parse_args()
    
    if args.action == 'add_channel':
        add_channel_command()
    else:
        return False
    
    return True 