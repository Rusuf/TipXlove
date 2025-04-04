from .. import socketio
from flask_socketio import join_room, leave_room
import logging

class SocketManager:
    """
    Socket manager to handle WebSocket events
    """
    
    @classmethod
    def handle_connect(cls, creator_id=None):
        """
        Handle client connection
        """
        if creator_id:
            cls.join_creator_room(creator_id)
        logging.debug(f"Client connected, creator_id: {creator_id}")
    
    @classmethod
    def handle_disconnect(cls):
        """
        Handle client disconnection
        """
        logging.debug("Client disconnected")
    
    @classmethod
    def join_creator_room(cls, creator_id):
        """
        Join a creator's room for receiving tips
        """
        if not creator_id:
            return
            
        room = f'creator_{creator_id}'
        join_room(room)
        logging.debug(f"Joined room: {room}")
    
    @classmethod
    def leave_creator_room(cls, creator_id):
        """
        Leave a creator's room
        """
        if not creator_id:
            return
            
        room = f'creator_{creator_id}'
        leave_room(room)
        logging.debug(f"Left room: {room}")
    
    @classmethod
    def emit_new_tip(cls, creator_id, tip_data):
        """
        Emit a new tip event to a creator's room
        
        Args:
            creator_id: The ID of the creator
            tip_data: Dictionary with tip details (name, amount, message)
        """
        room = f'creator_{creator_id}'
        socketio.emit('new_tip', tip_data, room=room)
        logging.debug(f"Emitted new_tip event to room {room}: {tip_data}")
    
    @classmethod
    def emit_tip_status(cls, creator_id, transaction_id, status, transaction=None):
        """
        Emit a tip status update
        
        Args:
            creator_id: The ID of the creator
            transaction_id: The ID of the transaction
            status: The new status (pending, completed, failed)
            transaction: Optional Transaction object for additional data
        """
        room = f'creator_{creator_id}'
        data = {
            'id': transaction_id,
            'status': status
        }
        
        if transaction:
            data.update({
                'mpesa_receipt': transaction.mpesa_receipt,
                'amount': float(transaction.amount),  # Ensure amount is serializable
                'phone_number': transaction.phone_number,
                'timestamp': transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.updated_at else None,
                'tipper_name': transaction.tipper_name,
                'message': transaction.message
            })
            
        socketio.emit('tip_status', data, room=room)
        logging.debug(f"Emitted tip_status event to room {room}: {data}")

# Register socket events
@socketio.on('connect')
def handle_connect():
    SocketManager.handle_connect()

@socketio.on('disconnect')
def handle_disconnect():
    SocketManager.handle_disconnect()

@socketio.on('join')
def handle_join(data):
    """
    Handle join room event
    Expected data: {'creator_id': id}
    """
    creator_id = data.get('creator_id')
    if creator_id:
        SocketManager.join_creator_room(creator_id)

@socketio.on('leave')
def handle_leave(data):
    """
    Handle leave room event
    Expected data: {'creator_id': id}
    """
    creator_id = data.get('creator_id')
    if creator_id:
        SocketManager.leave_creator_room(creator_id) 