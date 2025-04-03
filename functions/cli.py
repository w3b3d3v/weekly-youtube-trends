import argparse
from firebase_service import FirebaseService
from datetime import datetime

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

def show_channels_updates_command():
    """
    CLI command to show the last_updated field for all channels.
    Fetches and displays channel update information.
    """
    print("\n=== Canais e Datas de Atualização ===")
    
    try:
        # Initialize Firebase and fetch data
        firebase = FirebaseService()
        channels_data = firebase.get_channels_last_updated()
        
        if not channels_data:
            print("Nenhum canal encontrado com dados de atualização.")
            return
            
        # Print header
        print("-" * 110)
        print(f"{'ID':<25} | {'TÍTULO':<30} | {'STATUS':<10} | {'ÚLTIMA ATUALIZAÇÃO':<20}")
        print("-" * 110)
        
        # Print each channel
        for channel in channels_data:
            # Format the date for display
            date_str = channel['last_updated'].strftime("%d/%m/%Y %H:%M:%S") if isinstance(channel['last_updated'], datetime) else str(channel['last_updated'])
            
            # Truncate long titles and IDs
            title = channel['title'][:27] + "..." if len(channel['title']) > 30 else channel['title'].ljust(30)
            id_str = channel['id'][:22] + "..." if len(channel['id']) > 25 else channel['id'].ljust(25)
            status = channel['status'].ljust(10)
            
            print(f"{id_str} | {title} | {status} | {date_str}")
        
        print("-" * 110)
        print(f"Total de canais: {len(channels_data)}")
            
    except Exception as e:
        print(f"Erro ao buscar datas de atualização dos canais: {str(e)}")

def handle_cli_commands():
    """Handle CLI commands and arguments"""
    parser = argparse.ArgumentParser(description='YouTube Channel Manager')
    parser.add_argument('--action', type=str, help='Action to perform (add_channel, show_channels_updates)')
    
    args = parser.parse_args()
    
    if args.action == 'add_channel':
        add_channel_command()
    elif args.action == 'show_channels_updates':
        show_channels_updates_command()
    else:
        print("\nComandos disponíveis:")
        print("  --action add_channel           : Adicionar um novo canal do YouTube")
        print("  --action show_channels_updates : Mostrar datas de atualização dos canais")
        return False
    
    return True 