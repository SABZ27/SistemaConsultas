class EmailService:
    def enviar(self, para: str, asunto: str, contenido: str) -> None:
        print("========== EMAIL ==========")
        print(f"Para: {para}")
        print(f"Asunto: {asunto}")
        print(f"Contenido: {contenido}")
        print("===========================")