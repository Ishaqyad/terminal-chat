A simple multi client chat system built with Python sockets and threading.  


1. Open a terminal in the "client" folder.

2. Run the following:
   python client.py <server_ip> <port> <username> <password>
   Example:
   python client.py 127.0.0.1 5000 johndoe mypass

Commands:
PM - Send a public message to everyone.
DM - Send a private message to a single user.
EX - Fully exit.
es

Server sends structured JSON messages:

- broadcast → public messages
- direct → private messages
- active_users → current connected users
- info → confirmation messages
- error → command or user errors




No third party libraries required.
(socket, threading, json, sys).
