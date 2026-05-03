from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.core.config import settings
def init_collections():
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY,
        https=False,
        prefer_grpc=False,
    )
    collections = [
        (settings.QDRANT_COLLECTION_TICKETS, settings.EMBEDDING_DIM),
        (settings.QDRANT_COLLECTION_KB,      settings.EMBEDDING_DIM),
    ]
    for name, size in collections:
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
            print(f"Created collection: {name} (dim={size})")
        else:
            print(f"Already exists: {name}")
if __name__ == "__main__":
    init_collections()
