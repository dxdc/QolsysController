import logging
from typing import TYPE_CHECKING

from .broker import MqttBridgeBroker
from .client import MqttBridgeClient

if TYPE_CHECKING:
    from qolsys_controller.controller import QolsysController

LOGGER = logging.getLogger(__name__)


class MqttBridge:
    def __init__(self, controller: "QolsysController") -> None:
        self._controller = controller
        self._broker: MqttBridgeBroker | None = None
        self._client: MqttBridgeClient | None = None
        self._is_broker_running: bool = False
        self._is_client_running: bool = False

        self._version = "1"

        self._settings_topic = "settings"
        self._zone_topic = "zone"
        self._partition_topic = "partition"
        self._automation_topic = "automation"

        self._automation_command_topic = self.automation_topic + "/+/command"
        self._partition_command_topic = self.partition_topic + "/+/command"
        self._command_topics: list[str] = [
            self._automation_command_topic,
            self._partition_command_topic,
        ]

    async def start(self) -> bool:
        LOGGER.info("MQTT Bridge Starting ...")

        # Create MQTT Bridge Broker if not already created
        if not self._broker:
            self._broker = MqttBridgeBroker(self._controller)

        # Start MQTT Bridge Broker
        if not await self._broker.start():
            LOGGER.error("MQTT Bridge Broker failed to start. MQTT Bridge will not start.")
            return False

        # MQTT Bridge Broker is running
        self._is_broker_running = True

        # Create MQTT Bridge Client if not already created
        if not self._client:
            self._client = MqttBridgeClient(self)

        # Start MQTT Bridge Client
        if not await self._client.start():
            LOGGER.error("MQTT Bridge Client failed to connect. MQTT Bridge will not start.")
            return False

        self._is_client_running = True

        LOGGER.info("MQTT Bridge Running")
        return True

    async def shutdown(self) -> None:
        if self._client:
            await self._client.shutdown()
            self._is_client_running = False
        if self._broker:
            await self._broker.shutdown()
            self._is_broker_running = False

    @property
    def panel_unique_id(self) -> str:
        if self._controller.settings._mqtt_bridge_friendly_name != "":
            return self._controller.settings._mqtt_bridge_friendly_name
        return self._controller.panel.unique_id

    @property
    def version(self) -> str:
        return self._version

    @property
    def base_topic(self) -> str:
        return f"{self._controller.settings._mqtt_bridge_root_topic}/v{self.version}/{self.panel_unique_id}"

    @property
    def automation_topic(self) -> str:
        return f"{self.base_topic}/{self._automation_topic}"

    @property
    def partition_topic(self) -> str:
        return f"{self.base_topic}/{self._partition_topic}"

    @property
    def zone_topic(self) -> str:
        return f"{self.base_topic}/{self._zone_topic}"

    @property
    def settings_topic(self) -> str:
        return f"{self.base_topic}/{self._settings_topic}"

    @property
    def automation_command_topic(self) -> str:
        return self._automation_command_topic

    @property
    def partition_command_topic(self) -> str:
        return self._partition_command_topic
