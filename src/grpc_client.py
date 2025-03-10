import sys
import os
import grpc
import logging
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

# Configurar el registro
logging.basicConfig(level=logging.INFO)

# Agregar la ruta al directorio "generated" al sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '../generated'))
import xlerion_pb2 as xlerion_pb2
import xlerion_pb2_grpc as xlerion_pb2_grpc

# Ruta al archivo de credenciales
SERVICE_ACCOUNT_FILE = "../credentials/service_account.json" # Modified line

# Definir los alcances necesarios
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Cargar las credenciales de la cuenta de servicio con los alcances necesarios
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
credentials.refresh(Request())
access_token = credentials.token

# Crear un canal inseguro
def create_grpc_channel(endpoint):
    return grpc.insecure_channel(endpoint)

# Configuración del endpoint
endpoint = "localhost:50051"  # Cambiar a localhost para conectarse al servidor local

channel = create_grpc_channel(endpoint)
print("Conexión al servidor exitosa:", channel)

# Crear el stub del cliente
stub = xlerion_pb2_grpc.DataProcessingServiceStub(channel)

# Crear una solicitud y llamar al método GetGraphData
request = xlerion_pb2.Empty()
logging.info(f"Enviando solicitud GetGraphData")
response = stub.GetGraphData(request)
logging.info(f"Respuesta del servidor: {response}")



print("Respuesta del servidor:", response)
