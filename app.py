from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import uuid
import random

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Queue to store waiting users
waiting_users = []
# Room-to-players mapping
rooms = {}
# Room-to-current-turn mapping
rooms_turn = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"New connection: {request.sid}")
    waiting_users.append(request.sid)
    
    if len(waiting_users) >= 2:
        player1 = waiting_users.pop(0)
        player2 = waiting_users.pop(0)
        room = str(uuid.uuid4())
        rooms[room] = [player1, player2]
        join_room(room, player1)
        join_room(room, player2)
        
        print(f"Matched players {player1} and {player2} in room {room}")
        
        # Randomly choose who starts
        starter = random.choice([player1, player2])
        rooms_turn[room] = starter
        
        # Assign symbols accordingly
        if starter == player1:
            emit('match_found', {
                'room': room,
                'symbol': 'X',
                'opponent': player2,
                'starter': starter
            }, to=player1)
            emit('match_found', {
                'room': room,
                'symbol': 'O',
                'opponent': player1,
                'starter': starter
            }, to=player2)
        else:
            emit('match_found', {
                'room': room,
                'symbol': 'O',
                'opponent': player2,
                'starter': starter
            }, to=player1)
            emit('match_found', {
                'room': room,
                'symbol': 'X',
                'opponent': player1,
                'starter': starter
            }, to=player2)

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in waiting_users:
        waiting_users.remove(request.sid)

    # Find room containing this client
    for room_id, sids in list(rooms.items()):
        if request.sid in sids:
            # Inform opponent
            emit('opponent_disconnected', room=room_id)
            # Clean up
            del rooms[room_id]
            if room_id in rooms_turn:
                del rooms_turn[room_id]
            break

@socketio.on('game_move')
def handle_game_move(data):
    room = data['room']
    sender = data['sender']

    # Validate room and players
    players = rooms.get(room)
    if not players:
        return

    # Ensure it is sender's turn
    current_turn = rooms_turn.get(room)
    if sender != current_turn:
        # Ignore move if not sender's turn
        return

    # Switch turn to the other player
    next_turn = players[0] if current_turn == players[1] else players[1]
    rooms_turn[room] = next_turn

    # Broadcast move with nextTurn info
    emit('game_move', {
        'index': data['index'],
        'symbol': data['symbol'],
        'sender': sender,
        'nextTurn': next_turn
    }, room=room)

@socketio.on('chat_message')
def handle_chat(data):
    emit('chat_message', data, room=data['room'])

@socketio.on('signal')
def handle_webrtc_signal(data):
    emit('signal', data, room=data['room'])

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data['offer'], room=data['room'], include_self=False)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data['answer'], room=data['room'], include_self=False)

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    emit('ice-candidate', data['candidate'], room=data['room'], include_self=False)

@socketio.on('ready')
def handle_ready(room):
    emit('ready', room=room, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3430, debug=True)
