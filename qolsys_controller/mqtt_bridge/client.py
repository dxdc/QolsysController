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
        self._client_id = "InternalClient"
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._ready_event = asyncio.Event()
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=1000)
        self._registered = False

    async def start(self) -> bool:
        if self._task and not self._task.done():
            LOGGER.warning("MQTT Bridge Client: Client already running")
            return False

        self._stop_event.clear()
        self._ready_event.clear()
        self._task = asyncio.create_task(self._run())
        await self._ready_event.wait()
        return True

    async def shutdown(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Shutting down ...")

        self._stop_event.set()

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        LOGGER.debug("MQTT Bridge Client: Shutdown complete")

    def handle_event(self, event: Event) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            LOGGER.debug("MQTT Bridge Client: Queue is full. Dropping event: %s", event)

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            LOGGER.debug("MQTT Bridge Client: Connecting...")

            try:
                async with aiomqtt.Client(
                    hostname=self._bridge._controller.settings.plugin_ip,
                    port=self._bridge._controller.settings._mqtt_bridge_port,
                    identifier=self._client_id,
                ) as client:
                    LOGGER.debug("MQTT Bridge Client: Connected")

                    # Subscribe
                    for topic in self._bridge.command_topics:
                        LOGGER.debug("MQTT Bridge Client: Subscribing to topic: %s", topic)
                        await client.subscribe(topic, qos=self._bridge.mqtt_qos)

                    # Register events ONCE
                    if not self._registered:
                        self._register_events()
                        self._registered = True

                    # Refresh state to publish current values on startup
                    self._refresh_state()

                    # MQTT Bridge Client is connected and running
                    if not self._ready_event.is_set():
                        self._ready_event.set()

                    # Run listener + publisher concurrently
                    await self._run_connected(client)

            except asyncio.CancelledError:
                LOGGER.debug("MQTT Bridge Client: Shutting down ...")
                break

            except aiomqtt.MqttError as err:
                LOGGER.debug("MQTT Bridge Client: Connection error: %s", err)

            # Reconnect delay
            if not self._stop_event.is_set():
                LOGGER.debug("MQTT Bridge Client: Reconnecting in %s sec", self._bridge.mqtt_timeout)
                await asyncio.sleep(self._bridge.mqtt_timeout)

    async def _run_connected(self, client: aiomqtt.Client) -> None:
        listener = asyncio.create_task(self._listener(client))
        publisher = asyncio.create_task(self._publisher(client))

        LOGGER.debug("MQTT Bridge Client: Running")

        done, pending = await asyncio.wait(
            [listener, publisher],
            return_when=asyncio.FIRST_EXCEPTION,
        )

        # Cancel remaining task
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Raise exception if any
        for task in done:
            if not task.cancelled():
                exc = task.exception()
                if exc:
                    raise exc

    async def _listener(self, client: aiomqtt.Client) -> None:
        try:
            async for message in client.messages:
                if self._bridge._controller.settings.log_mqtt_messages:
                    if isinstance(message.payload, bytes):
                        LOGGER.debug(
                            "MQTT TOPIC: %s\n%s",
                            message.topic,
                            message.payload.decode(errors="ignore"),
                        )

                if message.topic.matches(self._bridge.automation_command_topic):
                    LOGGER.debug(
                        "MQTT Bridge Client: Automation command received: %s", message.payload.decode(errors="ignore")
                    )

                if message.topic.matches(self._bridge.partition_command_topic):
                    LOGGER.debug("MQTT Bridge Client: Partition command received: %s", message.payload.decode(errors="ignore"))

        except aiomqtt.MqttError as err:
            if self._stop_event.is_set():
                return

            LOGGER.debug("MQTT Bridge Client: Listener error - %s", err)
            raise

    async def _publisher(self, client: aiomqtt.Client) -> None:
        try:
            while True:
                event = await self._queue.get()

                payload = json.dumps(event.data)

                id = event.data.get("id")
                if event.type == QolsysNotification.ZONE_UPDATE:
                    topic = f"{self._bridge.zone_topic}/{id}"
                elif event.type == QolsysNotification.PARTITION_UPDATE:
                    topic = f"{self._bridge.partition_topic}/{id}"
                elif event.type == QolsysNotification.AUTOMATION_UPDATE:
                    topic = f"{self._bridge.automation_topic}/{id}"
                else:
                    continue

                await client.publish(topic, payload, qos=self._bridge.mqtt_qos, retain=True)

        except asyncio.CancelledError:
            raise

        except aiomqtt.MqttError as err:
            if self._stop_event.is_set():
                return

            LOGGER.debug("MQTT Bridge Client: Publisher error - %s", err)
            raise

    def _refresh_state(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Refreshing state ...")
        for zone in self._bridge._controller.state.zones:
            self.handle_event(Event(QolsysNotification.ZONE_UPDATE, zone, zone.to_dict_event()))

        for partition in self._bridge._controller.state.partitions:
            self.handle_event(Event(QolsysNotification.PARTITION_UPDATE, partition, partition.to_dict_event()))

        for autdev in self._bridge._controller.state.automation_devices:
            self.handle_event(Event(QolsysNotification.AUTOMATION_UPDATE, autdev, autdev.to_dict_event()))

    def _register_events(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Registering events ...")

        for zone in self._bridge._controller.state.zones:
            zone.register(QolsysNotification.ZONE_UPDATE, self.handle_event)

        for partition in self._bridge._controller.state.partitions:
            partition.register(QolsysNotification.PARTITION_UPDATE, self.handle_event)

        for autdev in self._bridge._controller.state.automation_devices:
            autdev.register(QolsysNotification.AUTOMATION_UPDATE, self.handle_event)
