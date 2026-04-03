import asyncio
import json
import logging
from typing import TYPE_CHECKING

import aiomqtt

from qolsys_controller.enum import QolsysNotification
from qolsys_controller.observable_v3 import Event

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from qolsys_controller.mqtt_bridge.bridge import MqttBridge


class MqttBridgeClient:
    def __init__(self, bridge: "MqttBridge") -> None:
        self._bridge = bridge
        self._client: aiomqtt.Client | None = None
        self._is_client_running: bool = False
        self._client_id = "InternalClient"
        self._listen_task: asyncio.Task | None = None

    async def start(self) -> bool:

        while True:
            LOGGER.debug("MQTT Bridge Client: Connecting ...")
            try:
                # Cancel existing listener task if any
                #if self._listen_task and not self._listen_task.done():
                #    self._listen_task.cancel()
                #    await asyncio.sleep(0)

                self._client = aiomqtt.Client(
                    hostname=self._bridge._controller.settings.plugin_ip,
                    port=self._bridge._controller.settings._mqtt_bridge_port,
                    clean_session=True,
                    timeout=self._bridge._controller.settings.mqtt_timeout,
                    identifier=self._client_id,
                )

                await self._client.__aenter__()
                LOGGER.debug("MQTT Bridge Client: Connected")

                # Subscribe to topics
                for topic in self._bridge._command_topics:
                    await self._client.subscribe(topic, qos=1)
                    LOGGER.debug("Subscribed to topic: %s", topic)

                # Register events asynchronously
                self._register_events_async()

                # Start background listener
                self._listen_task = asyncio.create_task(self._listen_messages())
                LOGGER.debug("MQTT Bridge Client: Starting Listenner")

                self._is_client_running = True
                return True

            except aiomqtt.MqttError as err:
                self._client = None
                self._is_client_running = False
                LOGGER.debug(
                    "MQTT Bridge Client Error - %s. Reconnecting in %s seconds...",
                    err,
                    self._bridge._controller.settings.mqtt_timeout,
                )
                await asyncio.sleep(self._bridge._controller.settings.mqtt_timeout)

    def _register_events_async(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Registering events ...")

        for zone in self._bridge._controller.state.zones:
            zone.register(QolsysNotification.ZONE_UPDATE, self.handle_event)
            asyncio.create_task(self.handle_event(Event(QolsysNotification.ZONE_UPDATE, zone, zone.to_dict_event())))

        for partition in self._bridge._controller.state.partitions:
            partition.register(QolsysNotification.PARTITION_UPDATE, self.handle_event)
            asyncio.create_task(self.handle_event(Event(QolsysNotification.PARTITION_UPDATE, partition, partition.to_dict_event())))

        for autdev in self._bridge._controller.state.automation_devices:
            autdev.register(QolsysNotification.AUTOMATION_UPDATE, self.handle_event)
            asyncio.create_task(self.handle_event(Event(QolsysNotification.AUTOMATION_UPDATE, autdev, autdev.to_dict_event())))

    async def _listen_messages(self) -> None:

        while True:
            if self._client is None:
                LOGGER.warning("MQTT client not available. Retrying connection...")
                await asyncio.sleep(self._bridge._controller.settings.mqtt_timeout)
                await self.start()  # reconnect
                continue

            try:
                async for message in self._client.messages:
                    if self._bridge._controller.settings.log_mqtt_messages:
                        if isinstance(message.payload, bytes):
                            LOGGER.debug("MQTT TOPIC: %s\n%s", message.topic, message.payload.decode())

                    # Handle automation commands
                    if message.topic.matches(self._bridge.automation_command_topic):
                        if isinstance(message.payload, bytes):
                            LOGGER.debug("Received Automation Command: %s", message.payload.decode())

                    # Handle partition commands
                    if message.topic.matches(self._bridge.partition_command_topic):
                        if isinstance(message.payload, bytes):
                            LOGGER.debug("Received Partition Command: %s", message.payload.decode())

            except aiomqtt.MqttError as err:
                LOGGER.debug(
                    "MQTT Listener Error - %s. Reconnecting in %s seconds...",
                    err,
                    self._bridge._controller.settings.mqtt_timeout,
                )
                self._client = None
                self._is_client_running = False
                await asyncio.sleep(self._bridge._controller.settings.mqtt_timeout)
                await self.start() 

    async def handle_event(self, event: Event) -> None:

        if not self._client:
            LOGGER.error("No MQTT client available to publish event: %s", event.type.name)
            return

        match event.type:
            case QolsysNotification.ZONE_UPDATE:
                zone = event.data
                id = zone.get("id")
                await self._client.publish(
                    f"{self._bridge.zone_topic}/{id}",
                    json.dumps(zone),
                    qos=1,
                    retain=True,
                )

            case QolsysNotification.PARTITION_UPDATE:
                partition = event.data
                id = partition.get("id")
                await self._client.publish(
                    f"{self._bridge.partition_topic}/{id}",
                    json.dumps(partition),
                    qos=1,
                    retain=True,
                )

            case QolsysNotification.AUTOMATION_UPDATE:
                autdev = event.data
                id = autdev.get("id")
                await self._client.publish(
                    f"{self._bridge.automation_topic}/{id}",
                    json.dumps(autdev),
                    qos=1,
                    retain=True,
                )

    async def shutdown(self) -> None:
        """Shutdown MQTT client and background tasks cleanly."""
        LOGGER.debug("MQTT Bridge Client: Shutting down ...")
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

        self._is_client_running = False
        LOGGER.debug("MQTT Bridge Client: Shutdown complete")
