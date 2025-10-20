"""Integración AISStream: conexión al WebSocket público y reenvío interno.

Este paquete mantiene una conexión viva a wss://stream.aisstream.io/v0/stream
y reenvía mensajes relevantes al frontend vía Socket.IO bajo el evento
"ais_update" o eventos más específicos en el futuro.
"""
