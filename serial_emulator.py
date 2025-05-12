#!/usr/bin/python3
# Serial emulator to check commands being sent to teensy

import os
import pty
import time
import fcntl
import termios
import msgpack
import binascii
from enum import Enum
import signal
import sys

class SerialReaderState(Enum):
    WAITING_BYTE1 = 0
    WAITING_BYTE2 = 1
    READING = 2

class ProtocolDecoder:
    def __init__(self, start_byte=0x00):
        self.start_byte = start_byte
        self.byte_buffer = b""
        self.mode = SerialReaderState.WAITING_BYTE1
        self.message_length = -1

    def process_bytes(self, new_bytes):
        """Process a new chunk of bytes from the serial port"""
        messages = []

        for byte in new_bytes:
            result = self.process_byte(byte)
            if result:
                try:
                    decoded = msgpack.unpackb(result)
                    messages.append(decoded)
                except Exception as e:
                    print(f"Failed to decode message: {e}")

        return messages

    def process_byte(self, byte):
        """Process a single byte according to the protocol state machine"""
        if self.mode == SerialReaderState.WAITING_BYTE1:
            if byte == self.start_byte:
                self.mode = SerialReaderState.WAITING_BYTE2

        elif self.mode == SerialReaderState.WAITING_BYTE2:
            self.message_length = byte
            self.mode = SerialReaderState.READING
            self.byte_buffer = b""

        elif self.mode == SerialReaderState.READING:
            self.byte_buffer += bytes([byte])
            if len(self.byte_buffer) == self.message_length:
                self.mode = SerialReaderState.WAITING_BYTE1
                return self.byte_buffer

        return None

def pretty_print_message(msg):
    """Format and print a decoded message"""
    print("\n--- DECODED MESSAGE ---")
    for key, value in msg.items():
        if isinstance(key, bytes):
            key = key.decode('utf-8')

        if isinstance(value, list):
            # Format arrays nicely
            if len(value) > 8:
                # For long arrays
                print(f"{key}: [", end="")
                for i in (value):
                    print(f"{i:.4f}" if isinstance(i, float) else i)
                print("]")
            else:
                # For shorter arrays
                print(f"{key}: [", end="")
                for i, v in enumerate(value):
                    end_char = ", " if i < len(value)-1 else ""
                    print(f"{v:.4f}" if isinstance(v, float) else v, end=end_char)
                print("]")
        else:
            print(f"{key}: {value}")

def format_raw_data(data):
    """Format raw data for display"""
    hex_str = binascii.hexlify(data).decode('utf-8')
    hex_formatted = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))

    text = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)

    return f"HEX: {hex_formatted}\nTXT: {text}"

class SerialEmulator:
    def __init__(self):
        self.master, self.slave = pty.openpty()
        self.tty_name = os.ttyname(self.slave)

        attrs = termios.tcgetattr(self.slave)
        attrs[0] = attrs[0] & ~(termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON)
        attrs[1] = attrs[1] & ~termios.OPOST
        attrs[2] = attrs[2] & ~(termios.CSIZE | termios.PARENB)
        attrs[2] = attrs[2] | termios.CS8
        attrs[3] = attrs[3] & ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        termios.tcsetattr(self.slave, termios.TCSANOW, attrs)

        fl = fcntl.fcntl(self.master, fcntl.F_GETFL)
        fcntl.fcntl(self.master, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        try:
            if os.path.exists('/dev/ttyACM0'):
                os.unlink('/dev/ttyACM0')
            os.symlink(self.tty_name, '/dev/ttyACM0')
            print(f"Created virtual serial port at /dev/ttyACM0 (linked to {self.tty_name})")
        except Exception as e:
            print(f"Error creating symlink: {e}")
            print("Try running with sudo")
            sys.exit(1)

        self.decoder = ProtocolDecoder(start_byte=0x00)

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, sig, frame):
        """Handle termination signals"""
        print("\nShutting down emulator...")
        try:
            os.unlink('/dev/ttyACM0')
        except:
            pass
        os.close(self.master)
        os.close(self.slave)
        sys.exit(0)

    def run(self):
        """Main emulator loop"""
        print("DJI Pupper Serial Emulator Running")
        print("Press Ctrl+C to exit")
        print("-" * 60)

        while True:
            try:
                try:
                    data = os.read(self.master, 1024)
                    if data:
                        print(f"\nReceived {len(data)} bytes:")
                        #print(format_raw_data(data))

                        messages = self.decoder.process_bytes(data)
                        for msg in messages:
                            pretty_print_message(msg)

                            if "pos" in msg or "cart_pos" in msg:
                                response = msgpack.packb(msg)
                                os.write(self.master, bytes([0x00, len(response)]) + response)
                except (OSError, BlockingIOError):
                    pass

                time.sleep(0.01)
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(0.1)

if __name__ == "__main__":
    print("Starting DJI Pupper Serial Emulator")
    emulator = SerialEmulator()
    emulator.run()
