from firebase_service import FirebaseService
from youtube_service import YouTubeService
from cli import handle_cli_commands
import time
from claude_service import ClaudeService
from datetime import datetime, timedelta, timezone

# Initialize global service instances
firebase_service = FirebaseService()
youtube_service = YouTubeService(firebase_service)
claude_service = ClaudeService(firebase_service)

def process_pending_channels():
    """Process channels with PENDING status to get their channel IDs"""
    print("\nVerificando canais pendentes...")
    pending_channels = firebase_service.get_pending_channels()
    print("pending_channels", pending_channels)
    
    for channel in pending_channels:
        print(f"\nProcessando canal pendente: {channel['title']}")
        try:
            channel_id = youtube_service.extract_channel_id_from_url(channel['url'])
            
            if channel_id:
                print(f"ID do canal encontrado: {channel_id}")
                # Update the channel document with the ID and change status to ACTIVE
                firebase_service.update_channel_status(
                    channel['doc_id'],
                    {
                        'channel_id': channel_id,
                        'status': 'ACTIVE'
                    }
                )
            else:
                print(f"❌ Não foi possível encontrar o ID para o canal: {channel['name']}")
                
        except Exception as e:
            print(f"❌ Erro ao processar canal pendente {channel['name']}: {str(e)}")
            continue

def check_master_summary_exists(firebase_service):
    """Check if a master summary exists for the last 7 days"""
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7))
    
    # Get the latest master summary
    latest_master = firebase_service.get_latest_master_summary()
    
    if latest_master and 'created_at' in latest_master:
        last_summary_date = latest_master['created_at'].timestamp()
        if time.time() - last_summary_date < 604800:  # 7 days in seconds
            print("Master summary already exists for the last 7 days")
            return True
            
    return False

def generate_master_from_existing_data(firebase_service, claude_service):
    """Generate master summary from existing channel summaries in the last 7 days"""
    print("\nGerando resumo consolidado a partir dos dados existentes...")
    
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7))
    
    # Get all channel summaries from the last 7 days
    weekly_summaries = firebase_service.get_recent_channel_summaries(seven_days_ago)
    
    if weekly_summaries:
        master_summary = claude_service.create_master_weekly_summary(weekly_summaries)
        
        if master_summary['has_master_summary']:
            consolidated_insight = {
                'content': master_summary['master_summary'],
                'type': 'consolidated_weekly',
                'title': 'Resumo Semanal Consolidado',
                'origin_id': 'consolidated_weekly',
                'created_at': datetime.now(timezone.utc)
            }
            firebase_service.save_insight(consolidated_insight)
            print("Resumo consolidado gerado e salvo com sucesso!")
            return True
            
    print("❌ Não foi possível gerar o resumo consolidado dos dados existentes")
    return False

def process_single_channel(channel):
    """Process a single channel and return its weekly summary if available"""
    print(f"\nProcessando canal: {channel['channel_id']}")
    
    try:
        # Skip if updated in last 24 hours
        if 'updated_at' in channel:
            last_updated = channel['updated_at'].timestamp()
            if time.time() - last_updated < 86400:
                print(f"Canal {channel['channel_id']} já foi atualizado nas últimas 24 horas.")
                return None
        
        # Get channel info and recent videos
        print("Buscando informações e vídeos recentes...")
        channel_info = youtube_service.get_channel_info(channel['channel_id'])
        videos, weekly_summary = youtube_service.get_recent_videos(channel['channel_id'])
        
        if channel_info:
            # Save channel info
            updated_channel = {
                **channel_info,
                'doc_id': channel['doc_id']
            }
            
            print(f"Atualizando informações do canal: {channel_info['title']}")
            firebase_service.save_channel_data(updated_channel)
        
        # After processing all videos, save the weekly summary if it exists
        if weekly_summary:
            insight_data = {
                'content': weekly_summary['weekly_summary'],
                'origin_id': channel['channel_id'],
                'type': 'channel',
                'title': f"{channel_info['title']}",
                'created_at': datetime.now(timezone.utc)
            }
            firebase_service.save_insight(insight_data)
            
            return {
                'channel_title': channel_info['title'],
                'summary': weekly_summary['weekly_summary']
            }
            
        return None
        
    except Exception as e:
        print(f"❌ Erro ao processar canal {channel['channel_id']}: {str(e)}")
        return None

def run_full_process():
    """Run the complete channel processing flow"""
    if handle_cli_commands():
        return
        
    print("Iniciando o processo de atualização...")
    
    # Process any pending channels first
    process_pending_channels()
    
    # Process active channels to update their summaries
    print("\nBuscando canais ativos do Firebase...")
    channels = firebase_service.get_active_channels()
    print(f"Encontrados {len(channels)} canais ativos para processar")
    
    all_weekly_summaries = []
    
    for channel in channels:
        weekly_summary = process_single_channel(channel)
        if weekly_summary:
            all_weekly_summaries.append(weekly_summary)
            
        print("Aguardando 1 segundo antes do próximo canal...")
        time.sleep(1)

    # Check if we already have a recent master summary
    if check_master_summary_exists(firebase_service):
        return
        
    # Try to generate master summary from existing data (including newly updated summaries)
    if generate_master_from_existing_data(firebase_service, claude_service):
        return
    
    # If we have new summaries from channel processing, try to generate master summary
    if all_weekly_summaries:
        print("\nGerando resumo consolidado de todos os canais...")
        master_summary = claude_service.create_master_weekly_summary(all_weekly_summaries)
        
        if master_summary['has_master_summary']:
            consolidated_insight = {
                'content': master_summary['master_summary'],
                'type': 'consolidated_weekly',
                'title': 'Resumo Semanal Consolidado',
                'origin_id': 'consolidated_weekly',
                'created_at': datetime.now(timezone.utc)
            }
            firebase_service.save_insight(consolidated_insight)
            print("Resumo consolidado gerado e salvo com sucesso!")
        else:
            print("❌ Não foi possível gerar o resumo consolidado")
    
    print("\nProcessamento finalizado!")

def main():
    run_full_process()

if __name__ == "__main__":
    main()