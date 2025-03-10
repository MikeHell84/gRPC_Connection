import sys
import os
import time
from concurrent import futures

# Add the path to the "generated" directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
generated_dir = os.path.join(current_dir, '../generated')
sys.path.append(generated_dir)

# Import generated files
import xlerion_pb2 as xlerion_pb2
import xlerion_pb2_grpc as xlerion_pb2_grpc
import grpc
from google.cloud import firestore

# Initialize Firestore
db = firestore.Client()

# gRPC server class
class DataProcessingService(xlerion_pb2_grpc.DataProcessingServiceServicer):
    def GetGraphData(self, request, context):
        try:
            users_ref = db.collection('users')
            users = users_ref.stream()

            data_points = []
            for user in users:
                user_dict = user.to_dict()
                if user_dict:  #check if the dictionary is not null
                  label = user_dict.get('name', 'Unnamed')
                  score = user_dict.get('score', 0)
                  if score is None:
                    score = 0
                  value = float(score)  # Procesa el campo "score"
                  data_points.append(xlerion_pb2.GraphDataPoint(label=label, value=value))

            return xlerion_pb2.GraphDataResponse(data_points=data_points)
        except (TypeError, AttributeError) as e:
            context.set_details(f"Error processing Firestore data: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return xlerion_pb2.GraphDataResponse()
        except Exception as e:
            context.set_details(f"Unexpected error in GetGraphData: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return xlerion_pb2.GraphDataResponse()



# gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) # Use futures.ThreadPoolExecutor
    xlerion_pb2_grpc.add_DataProcessingServiceServicer_to_server(DataProcessingService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server running on port 50051")
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
