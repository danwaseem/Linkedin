"""
LinkedIn Platform — Kafka Producer
Publishes domain events to Kafka topics using the standard JSON envelope.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer
from config import settings


class KafkaEventProducer:
    """Async Kafka producer for publishing domain events."""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Initialize and start the Kafka producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self.producer.start()

    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()

    async def publish(
        self,
        topic: str,
        event_type: str,
        actor_id: str,
        entity_type: str,
        entity_id: str,
        payload: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> str:
        """
        Publish an event following the standard Kafka envelope format.
        Returns the trace_id for correlation.
        """
        if not self.producer:
            raise RuntimeError("Kafka producer not started")

        trace_id = trace_id or str(uuid.uuid4())
        idempotency_key = str(uuid.uuid4())

        event = {
            "event_type": event_type,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": str(actor_id),
            "entity": {
                "entity_type": entity_type,
                "entity_id": str(entity_id),
            },
            "payload": payload,
            "idempotency_key": idempotency_key,
        }

        await self.producer.send_and_wait(
            topic=topic,
            value=event,
            key=str(entity_id),
        )

        return trace_id


# Singleton producer instance
kafka_producer = KafkaEventProducer()
