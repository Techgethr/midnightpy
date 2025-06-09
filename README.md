# MidnightPy

SDK en Python para interactuar con la red blockchain Midnight usando GraphQL.

## Características

- Soporte completo para async/await
- Tipado estático para mejor integración con IDEs
- Manejo robusto de errores con excepciones personalizadas
- Reintentos automáticos para consultas fallidas
- Validación de datos de entrada
- Funciones de utilidad para manipulación de datos blockchain
- Soporte para WebSocket para actualizaciones en tiempo real
- Decodificación de datos de transacciones usando ABI
- Estimación de costos de gas
- Documentación completa

## Instalación

1. Clona este repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Inicialización del Cliente

```python
import asyncio
from midnightpy import BlockchainClient

async def main():
    # Inicializa el cliente con tus endpoints GraphQL
    client = BlockchainClient(
        http_url="http://tu-endpoint-graphql/graphql",
        ws_url="ws://tu-endpoint-graphql/graphql",  # Opcional, para suscripciones
        timeout=30,  # Timeout en segundos
        retry_attempts=3  # Número de reintentos para consultas fallidas
    )
```

### Consultas Básicas

```python
    # Obtener el último bloque
    latest_block = await client.get_latest_block()
    print(f"Altura del último bloque: {latest_block.height}")
    print(f"Timestamp: {latest_block.datetime}")

    # Obtener un bloque por su hash
    block = await client.get_block_by_hash("0x123...")
    if block:
        print(f"Bloque encontrado en altura: {block.height}")

    # Obtener una transacción por su hash
    tx = await client.get_transaction_by_hash("0x456...")
    if tx:
        print(f"Estado de la transacción: {tx.apply_stage}")
```

### Interacción con Contratos

```python
    # Obtener acción de contrato
    action = await client.get_contract_action("0x789...")
    if action:
        print(f"Estado del contrato: {action.state}")

    # Estimar costo de gas
    gas_estimate = await client.estimate_gas(
        contract_address="0x789...",
        data="0x..."
    )
    print(f"Costo estimado de gas: {gas_estimate}")

    # Decodificar datos de transacción usando ABI
    abi = {
        # Tu ABI aquí
    }
    decoded = await client.decode_transaction("0x456...", abi)
    if decoded:
        print(f"Función llamada: {decoded['function']}")
```

### Suscripciones en Tiempo Real

```python
    # Suscribirse a nuevos bloques
    async for block in client.subscribe_to_blocks():
        print(f"¡Nuevo bloque recibido! Altura: {block.height}")

    # Suscribirse a acciones de contrato
    async for action in client.subscribe_to_contract_actions("0x789..."):
        print(f"¡Nueva acción de contrato! Estado: {action.state}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Manejo de Errores

```python
from midnightpy.exceptions import (
    BlockchainSDKException,
    GraphQLError,
    ConnectionError,
    ValidationError,
    SubscriptionError
)

async def main():
    try:
        client = BlockchainClient(...)
        block = await client.get_block_by_hash("invalid_hash")
    except ValidationError as e:
        print(f"Error de validación: {e}")
    except GraphQLError as e:
        print(f"Error de GraphQL: {e}")
        print(f"Errores específicos: {e.errors}")
    except ConnectionError as e:
        print(f"Error de conexión: {e}")
    except SubscriptionError as e:
        print(f"Error de suscripción: {e}")
    except BlockchainSDKException as e:
        print(f"Error general del SDK: {e}")
```

## Funciones de Utilidad

El SDK incluye varias funciones de utilidad para trabajar con datos blockchain:

```python
from midnightpy.utils import (
    validate_hex_address,
    validate_hash,
    format_hex,
    timestamp_to_datetime,
    format_contract_state,
    calculate_gas_estimate,
    decode_contract_data
)

# Validar direcciones y hashes
is_valid = validate_hex_address("0x123...")
is_valid = validate_hash("0x456...")

# Formatear valores hexadecimales
formatted = format_hex("123...")  # Añade '0x' si no está presente

# Convertir timestamps
datetime = timestamp_to_datetime(1234567890)

# Formatear estado de contrato
state = format_contract_state("0x789...")

# Calcular estimación de gas
gas = calculate_gas_estimate("0x...")

# Decodificar datos de contrato
decoded = decode_contract_data("0x...", abi)
```

## API Reference

### BlockchainClient

La clase principal para interactuar con la red blockchain.

#### Métodos

- `get_latest_block() -> Block`
  - Retorna el último bloque de la blockchain

- `get_block_by_hash(block_hash: str) -> Optional[Block]`
  - Retorna un bloque por su hash, o None si no se encuentra

- `get_transaction_by_hash(tx_hash: str) -> Optional[Transaction]`
  - Retorna una transacción por su hash, o None si no se encuentra

- `get_contract_action(address: str) -> Optional[ContractAction]`
  - Retorna la última acción de un contrato

- `estimate_gas(contract_address: str, data: str) -> int`
  - Estima el costo de gas para una interacción con contrato

- `decode_transaction(tx_hash: str, abi: Dict[str, Any]) -> Optional[dict]`
  - Decodifica una transacción usando el ABI del contrato

- `subscribe_to_blocks()`
  - Generador que produce nuevos bloques cuando son creados

- `subscribe_to_contract_actions(address: str)`
  - Generador que produce nuevas acciones de contrato

### Modelos de Datos

- `Block`
  - `hash: str`
  - `height: int`
  - `protocol_version: int`
  - `timestamp: int`
  - `author: Optional[str]`
  - `transactions: List[Transaction]`
  - `datetime: datetime` (propiedad)

- `Transaction`
  - `hash: str`
  - `protocol_version: int`
  - `apply_stage: str`
  - `identifiers: List[str]`
  - `raw: str`
  - `merkle_tree_root: str`
  - `contract_actions: List[ContractAction]`

- `ContractAction` (clase base)
  - `address: str`
  - `state: str`
  - `chain_state: str`
  - `transaction: Transaction`

- `ContractCall` (extiende ContractAction)
  - Campos adicionales:
    - `entry_point: str`
    - `deploy: ContractDeploy`

- `ContractDeploy` (extiende ContractAction)
- `ContractUpdate` (extiende ContractAction)

## Licencia

MIT 