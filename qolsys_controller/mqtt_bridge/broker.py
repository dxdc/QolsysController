import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from amqtt.broker import Broker
from amqtt.plugins.authentication import BaseAuthPlugin

LOGGER = logging.getLogger(__name__)
logging.getLogger("transitions.core").setLevel(logging.ERROR)
logging.getLogger("amqtt").setLevel(logging.ERROR)
logging.getLogger("amqtt.core").setLevel(logging.ERROR)
logging.getLogger("amqtt.broker").setLevel(logging.ERROR)
logging.getLogger("amqtt.plugins").setLevel(logging.ERROR)


if TYPE_CHECKING:
    from qolsys_controller.controller import QolsysController


class AuthPlugin(BaseAuthPlugin):
    def set_config(self, config):
        super().set_config(config)
        self.allowed_users = config.get("allowed_users", {})

    async def authenticate(self, username, password, **kwargs):
        if username == "admin" and password == "secret":
            return True
        return False

    @dataclass
    class Config:
        allowed_users: dict[str, str] = None


class MqttBridgeBroker:
    def __init__(self, controller: "QolsysController") -> None:
        self._controller = controller
        self._config: dict[str, Any] = self._build_config()
        self._broker: Broker = self._create_broker()

    async def start(self) -> bool:
        LOGGER.info(
            "MQTT Bridge Broker: Starting: %s:%s ...",
            self._controller.settings.plugin_ip,
            self._controller.settings._mqtt_bridge_port,
        )

        try:
            await self._broker.start()
            await self.wait_for_broker_start()
            return True

        except Exception as e:
            LOGGER.error("MQTT Bridge Broker: Error Starting: %s", e)
            return False

    async def wait_for_broker_start(self, timeout: int = 5) -> None:
        start_time = asyncio.get_event_loop().time()
        while self._broker.transitions.state != "started":
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("MQTT Bridge Broker did not start in time")
            await asyncio.sleep(0.05)
        LOGGER.info("MQTT Bridge Broker: Running")

    def _create_broker(self) -> Broker:
        broker = Broker(self._config)
        return broker

    def _build_config(self) -> None:
        # "cafile": "cert.pem",
        # "certfile": "cert.pem",
        # "keyfile": "key.pem",

        listeners = {
            "default": {
                "type": "tcp",
                "bind": f"{self._controller.settings.plugin_ip}:{self._controller.settings.mqtt_bridge_port}",
                "ssl": False,
                "max_connections": self._controller.settings.mqtt_bridge_max_connections,
            }
        }

        # Plugin selection
        if self._controller.settings.mqtt_bridge_allow_anonymous:
            plugins = {"amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": True}}
        else:
            plugins = {
                "qolsys_controller.mqtt_bridge.broker.AuthPlugin": {
                    "allowed_users": self._controller.settings.mqtt_bridge_allowed_users
                }
            }

        return {"listeners": listeners, "plugins": plugins}

    async def shutdown(self) -> None:
        LOGGER.info("MQTT Bridge Broker: Shutting down ...")
        await self._broker.shutdown()
        LOGGER.info("MQTT Bridge Broker: Shutdown complete")
