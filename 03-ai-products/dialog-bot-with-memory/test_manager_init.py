from pinecone_manager import PineconeManager

manager = PineconeManager()
print("PineconeManager успешно создан")

vector = manager.create_embedding("Привет, это тест эмбеддинга")
print(f"Длина эмбеддинга: {len(vector)}")
print("Первые 5 значений:", vector[:5])

