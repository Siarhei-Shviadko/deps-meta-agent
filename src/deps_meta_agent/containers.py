from typing import Any, Dict, Optional, Type, Union

from dependency_injector import containers, providers, resources
from deps_asb import ASBClient, ASBConsumer, ASBProducer
from deps_kafka import KafkaClient, KafkaConsumer, KafkaProducer
from deps_message_flow import MessagingDriverEnum
from deps_message_flow.commands.producer import CommandProducer
from deps_message_flow.events.publisher import DomainEventPublisher
from deps_message_flow.messaging.consumer import IMessageConsumer
from deps_message_flow.messaging.producer import IMessageProducer
from deps_rabbitmq import RabbitMQClient, RabbitMQConsumer, RabbitMQProducer

from deps_meta_agent.application import ChatService, CommandAgenticManifestService
from deps_meta_agent.application.agent_vendor_registration_service import (
    AgentVendorRegistrationService,
)
from deps_meta_agent.constants import (
    AGENT_VENDOR_DESCRIPTION,
    AGENT_VENDOR_NAME,
    PROJECT_NAME,
)
from deps_meta_agent.extras import DatabaseSession
from deps_meta_agent.infrastructure.adapters.agent_http_client import (
    HttpAgentStreamClient,
)
from deps_meta_agent.infrastructure.agent import (
    AgentCaller,
    MetaAgentOrchestrator,
    ModelProviderFactory,
    OrchestratorWorkflowFactory,
)
from deps_meta_agent.infrastructure.agent.settings import OrchestratorSettings
from deps_meta_agent.infrastructure.agentic_ai import AgenticAIClient
from deps_meta_agent.infrastructure.unit_of_work import (
    AbstractUnitOfWork,
    SqlAlchemyUnitOfWork,
)
from deps_meta_agent.messaging.dispatcher import make_message_dispatcher

MessagingClient = Union[ASBClient, KafkaClient, RabbitMQClient]


class MessageBrokerResource(resources.Resource):
    def init(
        self,
        driver_type: str,
        expected_driver: str,
        client: Type[MessagingClient],
        message_connection_string: str,
        **kwargs: Dict[str, Any],
    ) -> Optional[MessagingClient]:
        return client(message_connection_string, **kwargs) if driver_type == expected_driver else None

    def shutdown(self, resource: Optional[MessagingClient]) -> None:
        if resource:
            resource.close()


class MessageBrokers(containers.DeclarativeContainer):
    config = providers.Configuration()
    messaging_driver_settings = providers.Dependency(instance_of=object)

    broker_client: providers.Provider[MessagingClient] = providers.Selector(
        config.messaging_driver,
        asb=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.ASB.value,
            expected_driver=config.messaging_driver,
            client=ASBClient,
            message_connection_string=config.message_broker_connection_string,
            asb_settings=messaging_driver_settings,
        ),
        kafka=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.KAFKA.value,
            expected_driver=config.messaging_driver,
            client=KafkaClient,
            message_connection_string=config.message_broker_connection_string,
            settings=messaging_driver_settings,
        ),
        rabbitmq=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.RABBITMQ.value,
            expected_driver=config.messaging_driver,
            client=RabbitMQClient,
            message_connection_string=config.message_broker_connection_string,
            settings=messaging_driver_settings,
        ),
    )


class Messaging(containers.DeclarativeContainer):
    config = providers.Configuration()
    message_brokers = providers.DependenciesContainer()

    producer: providers.Provider[IMessageProducer] = providers.Selector(
        config.messaging_driver,
        asb=providers.Singleton(
            ASBProducer,
            client=message_brokers.broker_client,
            topic_name=config.messaging_driver_settings.topic_name,
        ),
        kafka=providers.Singleton(
            KafkaProducer,
            client=message_brokers.broker_client,
        ),
        rabbitmq=providers.Singleton(
            RabbitMQProducer,
            client=message_brokers.broker_client,
        ),
    )
    consumer: providers.Provider[IMessageConsumer] = providers.Selector(
        config.messaging_driver,
        asb=providers.Singleton(
            ASBConsumer,
            client=message_brokers.broker_client,
            topic_name=config.messaging_driver_settings.topic_name,
            custom_subscription_name=PROJECT_NAME,
        ),
        kafka=providers.Singleton(
            KafkaConsumer,
            client=message_brokers.broker_client,
        ),
        rabbitmq=providers.Singleton(
            RabbitMQConsumer,
            client=message_brokers.broker_client,
        ),
    )


class Core(containers.DeclarativeContainer):
    config = providers.Configuration()
    build_info: providers.Provider[Dict] = providers.Dict(
        {
            "build_tag": config.info.tag,
            "build_date": config.info.date,
            "commit_hash": config.info.hash,
        },
    )


class Datasources(containers.DeclarativeContainer):
    config = providers.Configuration()

    postgres_session: providers.Provider[DatabaseSession] = providers.Singleton(
        DatabaseSession,
        username=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.db,
        dialect=config.dialect,
        driver=config.driver,
        require_secure_transport=config.require_secure_transport,
        pool_size=config.pool_size,
    )


class Repositories(containers.DeclarativeContainer):
    config = providers.Configuration()
    datasources = providers.DependenciesContainer()


class Containers(containers.DeclarativeContainer):
    config = providers.Configuration()
    messaging_driver_settings = providers.Dependency(instance_of=object)

    datasources: providers.Container[Datasources] = providers.Container(
        Datasources,
        config=config.database,
    )

    repositories: providers.Container[Repositories] = providers.Container(
        Repositories,
        config=config,
        datasources=datasources,
    )

    core: providers.Container[Core] = providers.Container(Core, config=config)
    message_brokers: providers.Container[MessageBrokers] = providers.Container(
        MessageBrokers,
        config=config,
        messaging_driver_settings=messaging_driver_settings,
    )

    messaging: providers.Container[Messaging] = providers.Container(
        Messaging,
        config=config,
        message_brokers=message_brokers,
    )

    command_producer: providers.Singleton[CommandProducer] = providers.Singleton(
        CommandProducer,
        messaging.producer,
    )

    domain_event_publisher: providers.Singleton[DomainEventPublisher] = providers.Singleton(
        DomainEventPublisher,
        messaging.producer,
    )

    message_dispatcher: providers.Singleton[IMessageConsumer] = providers.Singleton(
        make_message_dispatcher,
        messaging.consumer,
        messaging.producer,
    )

    unit_of_work: providers.Singleton[AbstractUnitOfWork] = providers.Singleton(
        SqlAlchemyUnitOfWork,
        database_session=datasources.postgres_session,
    )

    command_agentic_manifest_service: providers.Singleton[CommandAgenticManifestService] = providers.Singleton(
        CommandAgenticManifestService,
        unit_of_work=unit_of_work,
        domain_event_publisher=domain_event_publisher,
    )

    agentic_ai_client: providers.Singleton[AgenticAIClient] = providers.Singleton(
        AgenticAIClient,
        base_url=config.agentic_ai_url,
        timeout=config.agentic_ai_timeout,
    )

    agent_vendor_registration_service: providers.Singleton[AgentVendorRegistrationService] = providers.Singleton(
        AgentVendorRegistrationService,
        agentic_ai_client=agentic_ai_client,
        agent_vendor_name=AGENT_VENDOR_NAME,
        agent_vendor_description=AGENT_VENDOR_DESCRIPTION,
        meta_agent_base_url=config.meta_agent_url,
    )

    agent_http_client: providers.Singleton[HttpAgentStreamClient] = providers.Singleton(
        HttpAgentStreamClient,
    )

    orchestrator_settings: providers.Factory[OrchestratorSettings] = providers.Factory(
        OrchestratorSettings,
        config.orchestrator,
    )

    model_provider_factory: providers.Singleton[ModelProviderFactory] = providers.Singleton(
        ModelProviderFactory,
        settings=orchestrator_settings,
    )

    agent_caller: providers.Singleton[AgentCaller] = providers.Singleton(
        AgentCaller,
        agent_client=agent_http_client,
    )

    orchestrator_workflow_factory: providers.Singleton[OrchestratorWorkflowFactory] = providers.Singleton(
        OrchestratorWorkflowFactory,
        llm=providers.Factory(lambda factory: factory.create_llm(), factory=model_provider_factory),
        settings=orchestrator_settings,
        agent_caller=agent_caller,
    )

    meta_agent_orchestrator: providers.Singleton[MetaAgentOrchestrator] = providers.Singleton(
        MetaAgentOrchestrator,
        workflow_factory=orchestrator_workflow_factory,
    )

    chat_service: providers.Singleton[ChatService] = providers.Singleton(
        ChatService,
        unit_of_work=unit_of_work,
        orchestrator=meta_agent_orchestrator,
    )
