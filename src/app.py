import sys
import os

# Add the path to the "generated" directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
generated_dir = os.path.join(current_dir, '../generated')
sys.path.append(generated_dir)

import unittest
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify, request
import grpc
from google.cloud import firestore
import xlerion_pb2 as xlerion_pb2
import xlerion_pb2_grpc as xlerion_pb2_grpc

# Flask app setup
app = Flask(__name__)

# Firestore client setup
db = firestore.Client()

# gRPC client setup
channel = grpc.insecure_channel('localhost:50051')
stub = xlerion_pb2_grpc.DataProcessingServiceStub(channel)

# Add the stub to app
app.stub = stub

#function for getting all the fields
def get_all_fields():
    users_ref = db.collection('users')
    users = users_ref.stream()
    all_user_fields = set()
    all_task_fields = set()

    for user in users:
        user_dict = user.to_dict()
        all_user_fields.update(user_dict.keys())
        for task in user_dict.get('tasks', []):
          all_task_fields.update(task.keys())

    return {'user': list(all_user_fields), 'task': list(all_task_fields)}

@app.route('/')
def index():
    return "Bienvenido al sistema de graficación con Flask, gRPC y Firestore."

@app.route('/getgraphdata', methods=['GET'])
def get_graph_data():
    try:
        # gRPC call
        response = app.stub.GetGraphData(xlerion_pb2.Empty())
        graph_data = []
        for point in response.data_points:
            graph_data.append({'label': point.label, 'value': point.value})
        return jsonify({'graph_data': graph_data})
    except grpc.RpcError as e:
        return f"gRPC error: {e}", 500

@app.route('/getdata', methods=['POST'])
def get_data():
    data = request.get_json()
    query = data.get('query')
    if query == "test":
        response_data = {'data': 'test response'}
    else:
        response_data = {'data': f'You sent: {query}'}
    return jsonify(response_data)

@app.route('/adddata', methods=['POST'])
def add_data():
    data = request.get_json()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    user_email = data.get('user_email')
    task_id = data.get('task_id')
    task_title = data.get('task_title')
    task_status = data.get('task_status')
    task_due_date = data.get('task_due_date')
    user_score = data.get('user_score')  # Get the user's score

    # Now save this data in Firestore
    doc_ref = db.collection('users').document(user_id)
    doc_ref.set({
      'name': user_name,
      'email': user_email,
      'score': float(user_score), # Add the user's score. This has to be a number.
      'tasks': firestore.ArrayUnion([{
        'id': task_id,
        'title': task_title,
        'status': task_status,
        'due_date': task_due_date
      }])
    }, merge=True)

    return jsonify({'message': 'Data added successfully'})

@app.route('/getfields')
def get_fields():
    fields_data = get_all_fields()
    return jsonify({'fields': fields_data})

@app.route('/getuserdata')
def get_user_data():
    users_ref = db.collection('users')
    users = users_ref.stream()
    user_data = []
    for user in users:
        user_dict = user.to_dict()
        user_data.append({
            'id': user.id,
            'name': user_dict.get('name'),
            'email': user_dict.get('email'),
            'tasks': user_dict.get('tasks', [])
        })
    return jsonify({'users': user_data})

@app.route('/verifydata')
def verify_data():
    users_ref = db.collection('users')
    users = users_ref.stream()
    verification_data = []
    for user in users:
        user_dict = user.to_dict()
        user_fields = {}
        for key, value in user_dict.items():
            user_fields[key] = type(value).__name__

        user_tasks_verification = []
        for task in user_dict.get('tasks', []):
            task_fields = {}
            for task_key, task_value in task.items():
                task_fields[task_key] = type(task_value).__name__
            user_tasks_verification.append({
                'field_count': len(task_fields),
                'field_types': task_fields
            })
        
        verification_data.append({
            'id': user.id,
            'name': user_dict.get('name'),
            'email': user_dict.get('email'),
            'field_count': len(user_fields),
            'field_types': user_fields,
            'tasks': user_tasks_verification
        })

    return jsonify({'verification_data': verification_data})

@app.route('/editdata', methods=['POST'])
def edit_data():
    print("edit data")
    # Here you would handle the data received from the frontend,
    # which could be a file and other form data.
    # For this example, we'll just send back a confirmation message.
    return jsonify({'message': 'Data received and processed'})

# Tests
class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.firestore.Client')
    @patch('app.grpc.insecure_channel')
    def test_index(self, mock_grpc_channel, mock_firestore_client):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), "Bienvenido al sistema de graficación con Flask, gRPC y Firestore.")
        mock_grpc_channel.assert_not_called()
        mock_firestore_client.assert_not_called()

    @patch('app.xlerion_pb2_grpc.DataProcessingServiceStub')
    @patch('app.firestore.Client')
    @patch('app.grpc.insecure_channel')
    def test_get_graph_data(self, mock_grpc_channel, mock_firestore_client, mock_stub):
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore_client.return_value = mock_db

        # Mock gRPC response
        mock_response = xlerion_pb2.GraphDataResponse(
            data_points=[
                xlerion_pb2.GraphDataPoint(label="User1", value=10.0),
                xlerion_pb2.GraphDataPoint(label="User2", value=20.0),
            ]
        )
        mock_instance=MagicMock()
        mock_instance.GetGraphData.return_value = mock_response
        mock_stub.return_value=mock_instance

        # Mock channel
        mock_channel = MagicMock()
        mock_grpc_channel.return_value = mock_channel
        #mock the channel

        # Make the request
        response = self.app.get('/getgraphdata')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        mock_instance.GetGraphData.assert_called_once_with(xlerion_pb2.Empty())

        # Check the JSON response data
        expected_data = {
            'graph_data': [
                {'label': 'User1', 'value': 10.0},
                {'label': 'User2', 'value': 20.0},
            ]
        }
        self.assertEqual(response.get_json(), expected_data)

    @patch('app.xlerion_pb2_grpc.DataProcessingServiceStub')
    @patch('app.firestore.Client')
    @patch('app.grpc.insecure_channel')
    def test_get_graph_data_empty_response(self, mock_grpc_channel, mock_firestore_client, mock_stub):
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore_client.return_value = mock_db

        # Mock gRPC response
        mock_response = xlerion_pb2.GraphDataResponse(data_points=[])
        mock_instance=MagicMock()
        mock_instance.GetGraphData.return_value = mock_response
        mock_stub.return_value=mock_instance

        # Mock channel
        mock_channel = MagicMock()
        mock_grpc_channel.return_value = mock_channel

        # Make the request
        response = self.app.get('/getgraphdata')

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        mock_instance.GetGraphData.assert_called_once_with(xlerion_pb2.Empty())

        # Check the JSON response data
        expected_data = {'graph_data': []}
        self.assertEqual(response.get_json(), expected_data)

    @patch('app.xlerion_pb2_grpc.DataProcessingServiceStub')
    @patch('app.firestore.Client')
    @patch('app.grpc.insecure_channel')
    def test_get_graph_data_grpc_exception(self, mock_grpc_channel, mock_firestore_client, mock_stub):
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore_client.return_value = mock_db

        # Mock gRPC exception
        mock_instance=MagicMock()
        mock_instance.GetGraphData.side_effect = grpc.RpcError("gRPC Error")
        mock_stub.return_value=mock_instance


        # Mock channel
        mock_channel = MagicMock()
        mock_grpc_channel.return_value = mock_channel

        # Make the request
        response = app.stub.GetGraphData(xlerion_pb2.Empty())
        # Assertions
        self.assertEqual(response.status_code, 500)
        mock_instance.GetGraphData.assert_called_once_with(xlerion_pb2.Empty())

    @patch('app.xlerion_pb2_grpc.DataProcessingServiceStub')
    @patch('app.firestore.Client')
    @patch('app.grpc.insecure_channel')
    def test_get_graph_data_grpc_exception_generic_message(self, mock_grpc_channel, mock_firestore_client, mock_stub):
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore_client.return_value = mock_db

        # Mock gRPC exception
        mock_instance=MagicMock()
        mock_instance.GetGraphData.side_effect = grpc.RpcError()
        mock_stub.return_value=mock_instance

        # Mock channel
        mock_channel = MagicMock()
        mock_grpc_channel.return_value = mock_channel

        # Make the request
        response = self.app.get('/getgraphdata')

        # Assertions
        self.assertEqual(response.status_code, 500)
        mock_instance.GetGraphData.assert_called_once_with(xlerion_pb2.Empty())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    unittest.main()
