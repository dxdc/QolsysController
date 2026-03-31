import asyncio
import json
import logging
from typing import TYPE_CHECKING

import aiomqtt
from aiomqtt.types import P

from qolsys_controller.enum import QolsysEvent
from qolsys_controller.observable_v3 import Event

LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from qolsys_controller.controller import QolsysController


class MqttBridgeClient:
    def __init__(self, controller: "QolsysController") -> None:
        self._controller = controller
        self._mqtt_bridge_client: aiomqtt.Client | None = None
        self._mqtt_bridge_client_running: bool = False
        self._client_id = "InternalClient"
        self._reconnect: bool = True

        self.mqtt_bridge_task_client_connect_label: str = "mqtt_bridge_task_client_connect"
        self.mqtt_bridge_task_client_listen_label: str = "mqtt_bridge_task_client_listen"
        self.mqtt_bridge_task_client_write_label: str = "mqtt_bridge_task_client_write"

    async def start(self) -> bool:
        while True:
            LOGGER.debug("MQTT Bridge Client: Connecting ...")

            try:
                # Cancel any existing MQTT Bridge Client tasks before starting new ones
                self._controller._task_manager.cancel(self.mqtt_bridge_task_client_listen_label)
                self._controller._task_manager.cancel(self.mqtt_bridge_task_client_write_label)

                self._mqtt_bridge_client = aiomqtt.Client(
                    hostname=self._controller.settings.plugin_ip,
                    port=self._controller.settings._mqtt_bridge_port,
                    clean_session=True,
                    timeout=self._controller.settings.mqtt_timeout,
                    identifier=self._client_id,
                )

                await self._mqtt_bridge_client.__aenter__()
                LOGGER.debug("MQTT Bridge Client: Connected")

                await self._controller._task_manager.run(self.writer(), self.mqtt_bridge_task_client_write_label)
                await self._controller._task_manager.run(self.listenner(), self.mqtt_bridge_task_client_listen_label)
                LOGGER.debug("MQTT Bridge Client: Running")
                return True

            except aiomqtt.MqttError as err:
                # Receive pannel network error
                self._mqtt_bridge_client_running = False
                # self.connected_observer.notify()
                self._mqtt_bridge_client = None

                if self._reconnect:
                    LOGGER.debug(
                        "MQTT Bridge Client Error - %s Connect - Reconnecting in %s seconds ... ...",
                        err,
                        self._controller.settings.mqtt_timeout,
                    )
                    await asyncio.sleep(self.settings.mqtt_timeout)

        LOGGER.debug("MQTT Bridge Client Connected")
        return self._mqtt_bridge_client_running

    async def listenner(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Starting Listenner ...")
        pass

    async def handle_event(self, event: Event) -> None:
        match event.type:
            case QolsysEvent.EVENT_PANEL_ZONE_UPDATE:
                zone = event.data
                zone_id = zone.get("id")
                LOGGER.debug("MQTT Bridge Client: Zone Update: %s", zone_id)
                await self._mqtt_bridge_client.publish(
                    f"panel/{self._controller.panel.unique_id}/zone/{zone_id}", json.dumps(zone), qos=1, retain=True
                )

            case QolsysEvent.EVENT_PANEL_PARTITION_UPDATE:
                partition = event.data
                partition_id = partition.get("id")
                LOGGER.debug("MQTT Bridge Client: Partition Update: %s", partition_id)
                await self._mqtt_bridge_client.publish(
                    f"panel/{self._controller.panel.unique_id}/partition/{partition_id}",
                    json.dumps(partition),
                    qos=1,
                    retain=True,
                )

            case QolsysEvent.EVENT_AUTDEV_DEVICE_UPDATE:
                autdev = event.data
                autdev_id = autdev.get("id")
                LOGGER.debug("MQTT Bridge Client: Automation Device Update: %s", autdev_id)
                await self._mqtt_bridge_client.publish(
                    f"panel/{self._controller.panel.unique_id}/automation/{autdev_id}",
                    json.dumps(autdev),
                    qos=1,
                    retain=True,
                )

    async def writer(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Starting Writer ...")

        # Register all zone for updates
        for zone in self._controller.state.zones:
            zone._observer_v3.register(QolsysEvent.EVENT_PANEL_ZONE_UPDATE, self.handle_event)

        for partition in self._controller.state.partitions:
            partition._observer_v3.register(QolsysEvent.EVENT_PANEL_PARTITION_UPDATE, self.handle_event)

        for autdev in self._controller.state.automation_devices:
            autdev._observer_v3.register(QolsysEvent.EVENT_AUTDEV_DEVICE_UPDATE, self.handle_event)

        # Create initial state for all zones
        for zone in self._controller.state.zones:
            await zone.notify_full()

        for partition in self._controller.state.partitions:
            await partition.notify_full()

        for autdev in self._controller.state.automation_devices:
            await autdev.notify_full()

    async def shutdown(self) -> None:
        LOGGER.debug("MQTT Bridge Client: Shutting down ...")
        if self._mqtt_bridge_client:
            await self._mqtt_bridge_client.__aexit__(None, None, None)
            self._mqtt_bridge_client = None
            self._mqtt_bridge_client_running = False
            LOGGER.debug("MQTT Bridge Client: Shutdown complete")
