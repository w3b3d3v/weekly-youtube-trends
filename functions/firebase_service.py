import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from config import FIREBASE_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS

class FirebaseService:
    def __init__(self):
        print("Inicializando serviço do Firebase...")
        
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            # When running in Cloud Functions, the environment is already authenticated
            # Only use credentials file when running locally
            if GOOGLE_APPLICATION_CREDENTIALS:
                print(f"Usando credenciais do arquivo local")
                cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
                firebase_admin.initialize_app(cred, {
                    'projectId': FIREBASE_PROJECT_ID,
                })
            else:
                print("Usando autenticação do ambiente cloud")
                firebase_admin.initialize_app()
                
        self.db = firestore.client()

    def get_channels(self):
        """Get all channels from Firestore"""
        print("Buscando lista de canais do Firestore...")
        channels_ref = self.db.collection('channels')
        channels = [doc.id for doc in channels_ref.stream()]
        print(f"Total de canais encontrados: {len(channels)}")
        return channels

    def save_channel_data(self, channel_data):
        """Save or update channel data"""
        doc_id = channel_data.pop('doc_id', None)  # Remove doc_id from data to be saved
        if not doc_id:
            print("❌ Erro: doc_id não fornecido para atualização do canal")
            return
        
        print(f"Atualizando dados do canal: {channel_data.get('title', '')}")
        channel_ref = self.db.collection('channels').document(doc_id)
        channel_data['updated_at'] = datetime.now()
        channel_ref.set(channel_data, merge=True)

    def save_video_data(self, video_data):
        """Save or update video data"""
        print(f"Salvando dados do vídeo: {video_data['title']}")
        video_ref = self.db.collection('videos').document(video_data['id'])
        video_data['updated_at'] = datetime.now()
        video_ref.set(video_data, merge=True)

    def get_channel(self, channel_id):
        """Get a specific channel from Firestore"""
        print(f"Buscando canal específico: {channel_id}")
        channel_ref = self.db.collection('channels').document(channel_id)
        doc = channel_ref.get()
        return doc.to_dict() if doc.exists else None

    def get_video(self, video_id):
        """Get a specific video from Firestore"""
        video_ref = self.db.collection('videos').document(video_id)
        doc = video_ref.get()
        exists = doc.exists
        print(f"Verificando vídeo {video_id}: {'Existe' if exists else 'Não existe'}")
        return doc.to_dict() if exists else None

    def add_channel(self, channel_name, channel_url):
        """Add a new channel to Firestore with PENDING status"""
        channel_data = {
            "title": channel_name,
            "url": channel_url,
            "status": "PENDING",
            "created_at": datetime.now(),
            "platform": "Youtube"
        }
        
        return self.db.collection('channels').add(channel_data)

    def get_pending_channels(self):
        """Get all channels with PENDING status"""
        print("Buscando canais pendentes do Firestore...")
        channels_ref = self.db.collection('channels')
        pending_channels = channels_ref.where(filter=firestore.FieldFilter('status', '==', 'PENDING')).stream()
        
        channels = []
        for doc in pending_channels:
            channel_data = doc.to_dict()
            channel_data['doc_id'] = doc.id
            channels.append(channel_data)
        
        print(f"Total de canais pendentes encontrados: {len(channels)}", channels)
        return channels

    def get_active_channels(self):
        """Get all channels with ACTIVE status"""
        print("Buscando canais ativos do Firestore...")
        channels_ref = self.db.collection('channels')
        active_channels = channels_ref.where(filter=firestore.FieldFilter('status', '==', 'ACTIVE')).stream()
        
        channels = []
        for doc in active_channels:
            channel_data = doc.to_dict()
            channel_data['doc_id'] = doc.id
            channels.append(channel_data)
        
        print(f"Total de canais ativos encontrados: {len(channels)}")
        return channels

    def update_channel_status(self, doc_id, update_data):
        """Update channel status and other fields"""
        print(f"Atualizando canal {doc_id} com: {update_data}")
        channel_ref = self.db.collection('channels').document(doc_id)
        channel_ref.update(update_data)

    def get_latest_prompt(self):
        """Get the most recent prompt document from Firestore"""
        print("Buscando prompt mais recente do Firestore...")
        prompts_ref = self.db.collection('prompts')
        # Get the latest prompt ordered by timestamp
        latest_prompt = prompts_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(1).stream()
        
        # Get the first (and only) document
        for doc in latest_prompt:
            return doc.to_dict()
        return None

    def save_insight(self, insight_data):
        """Save a new insight to Firestore"""
        print(f"Salvando insight para: {insight_data.get('origin_id', 'Unknown')}")
        insight_ref = self.db.collection('insights').document()
        insight_data['created_at'] = datetime.now()
        insight_ref.set(insight_data)

    def get_insight_by_origin(self, origin_id):
        """Get an insight by its origin_id"""
        print(f"Verificando insight para origin_id: {origin_id}")
        insights_ref = self.db.collection('insights')
        insights = insights_ref.where(filter=firestore.FieldFilter('origin_id', '==', origin_id)).limit(1).stream()
        
        for doc in insights:
            return doc.to_dict()
        return None

    def get_latest_master_summary(self):
        """Get the latest master summary from insights collection"""
        insights_ref = self.db.collection('insights')
        query = (insights_ref
                 .where(filter=firestore.FieldFilter('type', '==', 'consolidated_weekly'))
                 .stream())
                 
        # Get all consolidated weekly summaries and find the most recent one
        latest_summary = None
        latest_timestamp = None
        
        for doc in query:
            data = doc.to_dict()
            if 'created_at' in data:
                if not latest_timestamp or data['created_at'] > latest_timestamp:
                    latest_timestamp = data['created_at']
                    latest_summary = data
        
        return latest_summary

    def get_recent_channel_summaries(self, after_date):
        """Get channel summaries created after the specified date"""
        insights_ref = self.db.collection('insights')
        query = (insights_ref
                 .where(filter=firestore.FieldFilter('type', '==', 'channel'))
                 .stream())
                 
        summaries = []
        for doc in query:
            data = doc.to_dict()
            # Filter by date in memory instead of in query
            if 'created_at' in data and data['created_at'] >= after_date:
                summaries.append({
                    'channel_title': data.get('title', 'Unknown Channel'),
                    'summary': data.get('content', '')
                })
        return summaries

    def get_youtube_transcript_token(self):
        """Get the YouTube transcript bearer token from Firestore"""
        print("Buscando token de transcrição do YouTube...")
        token_ref = self.db.collection('tokens').limit(1).stream()
        for doc in token_ref:
            return doc.to_dict().get('token')
        return None