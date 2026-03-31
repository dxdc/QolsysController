import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .broker import MqttBridgeBroker
from .client import MqttBridgeClient


if TYPE_CHECKING:
    from qolsys_controller.controller import QolsysController

LOGGER = logging.getLogger(__name__)


class MqttBridge:
    def __init__(self, controller: "QolsysController") -> None:
        self._controller = controller
        self._mqtt_broker = MqttBridgeBroker(controller)
        self._mqtt_client = MqttBridgeClient(controller)
        self._is_mqtt_brige_broker_running: bool = False
        self._is_mqtt_brige_client_running: bool = False

    async def start(self) -> bool:
        LOGGER.info(
            "MQTT Bridge Starting ...",
        )

        # Create MQTT Bridge Broker if not already created
        if not self._mqtt_broker:
            self._mqtt_broker = MqttBridgeBroker(self._controller)

        # Start MQTT Bridge Broker
        if not await self._mqtt_broker.start():
            LOGGER.error("MQTT Bridge Broker failed to start. MQTT Bridge will not start.")
            return False

        # MQTT Bridge Broker is running
        self._is_mqtt_brige_broker_running = True

        # Create MQTT Bridge Client if not already created
        if not self._mqtt_client:
            self._mqtt_client = MqttBridgeClient(self._controller)

        # Start MQTT Bridge Client
        if not await self._mqtt_client.start():
            LOGGER.error("MQTT Bridge Client failed to connect. MQTT Bridge will not start.")
            return False

        # MQTT Bridge Client is running
        self._is_mqtt_brige_client_running = True

        return True

    async def shutdown(self) -> None:
        if self._mqtt_client:
            await self._mqtt_client.shutdown()
            self._is_mqtt_brige_client_running = False
        if self._mqtt_broker:
            await self._mqtt_broker.shutdown()
            self._is_mqtt_brige_broker_running = False
