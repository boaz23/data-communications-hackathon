"""Client logic for game lookup

Contains the logic of the client needed to look for game offers.

Functions:
    * look_for_game():
        Looks for a game offers from a server and returns its
        address and port
"""

import socket

import config
import network
import coder
import util
from socket_address import SocketAddress

# This is the address which we will listen for packets
_game_offer_recv_addr = SocketAddress(network.broadcast_addr(), config.GAME_OFFER_PORT)


def look_for_game():
    """Looks for a game offer and returns the server with the port

    Initiates a UDP socket and listens for a game offer and
    returns the server with the port.
    """

    print(f"waiting for game offer, listening on {_game_offer_recv_addr}")
    game_offer_socket = None
    try:
        game_offer_socket = _init_game_offer_socket()
        server_addr = _listen_for_game_offets(game_offer_socket)
    finally:
        if game_offer_socket is not None:
            game_offer_socket.close()
    return server_addr


def _init_game_offer_socket():
    """Initiates the socket

    Initiates the UDP socket used to listen for packets.
    """
    game_offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    game_offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    game_offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    game_offer_socket.bind(_game_offer_recv_addr.to_tuple())
    return game_offer_socket


def _listen_for_game_offets(game_offer_socket):
    server_addr = None
    while server_addr is None:
        server_addr = _recv_game_offer(game_offer_socket)
    return server_addr


def _recv_game_offer(game_offer_socket):
    # TODO: support padding
    """Receive game offer and return it

    Blocks to receive UDP packets.
    Checks if they represent a proper game offer, and if so,
    returns the server which sent the offer toghether with the port it
    said we should connected to (the port in the message)
    """
    try:
        message_bytes, server_addr = game_offer_socket.recvfrom(config.GAME_OFFER_RECV_BUFFER_SIZE)
    except OSError:
        # Error while reading from the socket, nothing to do really,
        # just keep listening for more offers
        print("error receiving game offer, continue to look for game offers...")
        return None

    server_addr = SocketAddress(server_addr)
    print(f"received data from {server_addr}")
    port = _decode_message(message_bytes)
    if port is None:
        print(f"offer data: {util.bytes_to_string(message_bytes)}")
        return None
    return SocketAddress(server_addr.host, port)


def _decode_message(message_bytes):
    if len(message_bytes) != config.GAME_OFFER_MSG_SIZE:
        util.print_err(f"invalid game offer: length {len(message_bytes)}")
        return None
    magic_coockie = coder.decode_int(message_bytes[0:4])
    if magic_coockie != config.MAGIC_COOKIE:
        util.print_err(f"invalid game offer: cookie {hex(magic_coockie).upper()}")
        return None
    msg_type = coder.decode_int(message_bytes[4:5])
    if msg_type != config.MSG_TYPE_OFFER:
        util.print_err(f"invalid game offer: message type {hex(msg_type).capitalize()}")
        return None
    port = coder.decode_int(message_bytes[5:7])
    return port


if __name__ == "__main__":
    def main():
        try:
            while True:
                server_addr = look_for_game()
                print(f"received offer from {server_addr}")
        except KeyboardInterrupt:
            pass

    main()
