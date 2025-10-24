Run:
python server.py <port>
Example: python server.py 5000




Features:
- Multithreaded TCP server for the chat app. 
- Handles multiple clients, login, registration, and message routing through JSON.
- Stores users in users.db
- Broadcasts public (PM) and direct (DM) messages
- Updates active user lists on login/logout

Python standard libraries only
(socket, threading, json, sys).
