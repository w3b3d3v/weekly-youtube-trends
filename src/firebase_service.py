import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

class FirebaseService:
    def __init__(self):
        print("Inicializando serviço do Firebase...")
        # Initialize Firebase Admin SDK with your service account
        # Load your service account's private key JSON file
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        print(f"Usando credenciais do arquivo: {cred_path}")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        })
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
            "name": channel_name,
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
        
        print(f"Total de canais pendentes encontrados: {len(channels)}")
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