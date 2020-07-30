## SPEID

[![Test](https://github.com/cuenca-mx/speid/workflows/Test/badge.svg)](https://github.com/cuenca-mx/speid/actions?query=workflow%3ATest)
[![codecov](https://codecov.io/gh/cuenca-mx/speid/branch/master/graph/badge.svg)](https://codecov.io/gh/cuenca-mx/speid)
[![](https://images.microbadger.com/badges/image/cuenca/speid:1.9.4.svg)](https://microbadger.com/images/cuenca/speid:1.9.4 "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/cuenca/speid:1.9.4.svg)](https://microbadger.com/images/cuenca/speid:1.9.4 "Get your own version badge on microbadger.com")
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Una forma robusta de comunicarse con STP, utilizando la librería 
[stpmex](https://pypi.org/project/stpmex/) para el manejo de transferencias 
eléctronicas. Hay dos puntos importantes:

- **Envío de transferencias** Debe haber un backend que coloque las órdenes de 
transferencias en una cola de RabbitMQ. SPEID tomará las órdenes de ahí para enviarlas 
por STP. En caso de cualquier falla, la orden se vuelve a colocar en la cola y se 
reintenta hasta 3 veces. En caso de que la orden no pueda ser enviada, esta se 
queda en la cola para poder ser revisada manualmente. Por otro lado, cuando la orden
 es enviada con éxito, se recibe la respuesta de STP en `orden_events` para hacer el 
 llamado al backend y confirmar o cancelar la orden.

- **Recepción de transferencias** Las órdenes se reciben en `ordenes` y hace un llamado
al backend para poder recibir las órdenes, en caso de un error en el backend la orden 
se confirma pero se mantiene en la base de datos para poder ser reprocesada 
porteriormente.
 

### Requerimientos

- Una cuenta de STP
- Python v3 o superior.
- Docker
- Sentry
- Un backend de donde recibir y enviar las órdenes

### Instalación

El archivo `env.template` contiene todos los parámetros necesarios para hacer funcionar 
SPEID, es necesario completar los faltantes como las credenciales de STP, la URL de 
Sentry o la URL de MongoDB para realizar la conexión.

Después de esto, solo es necesario utilizar un gestor de contenedores para ejecutar 
la imagen de Docker incluida en el proyecto.

En caso de ser necesario ejectuarlo en una máquina local, copiar el archivo 
`env.template` a `.env` y sustituir las credenciales de STP y Sentry. Posteriormente, 
utilizar el archivo `docker-compose` incluido que levanta todos los servicios necesarios.
``` bash
docker-compose up
```

### Test

Para ejecutar los test localmente, se puede utilizar y utilizar la variable de ambiente `DATABASE_URI` 
por `mongomock://localhost:27017/db`:

```bash
make install-dev
make test
```

Sin embargo, eso implica tener las variables de entorno en el equipo de desarrollo 
utilizado, tammbién se puede realizar todo en Docker usando la variable de ambiente 
`DATABASE_URI` con `mongodb://db/db`:

```bash
cp env.template .env
make docker-test
```

También se puede ejecutar el servicio y dar una línea de comandos dentro del contenedor
para poder ejecutar instrucciones como el acceso a la base de datos, etc.

```bash
cp env.template .env
make docker-shell
```

Ambos comandos ejecutan todas las instancias necesarias para funcionar y las cierran
al terminar.


### Uso básico

#### Recibir una orden

Cuando se recibe una nueva orden SPEI, STP hace una llamada al 
servicio `/ordenes`. Se crea una transacción en la tabla `transactions`
y se asocia un evento tipo `create`. Posteriormente, se hace un POST al endpoint 
definido en la variable de ambiente `CALLBACK_URL`. El servicio aguarda 15 segundos a 
obtener una respuesta la cual es almacenada en un nuevo Evento asociado a la 
Transacción y se responde a STP.

El cuerpo del mensaje almacenado en RabbitMQ es como sigue:

```python
{
'orden_id': 6440277,                              # Orden ID de STP 
'fecha_operacion': 20181008,                     
'institucion_ordenante': '072',                  # Código del banco definido por SPEI
'institucion_beneficiaria': '646',               # Código del banco definido por SPEI
'clave_rastreo': '7279MAP6201810060648658333', 
'monto': 1020,                                 # En centavos 
'nombre_ordenante': 'RICARDO SANCHEZ CASTILLO', 
'tipo_cuenta_ordenante': 40, 
'cuenta_ordenante': '072691004495711499', 
'rfc_curp_ordenante': 'SACR891125M47', 
'nombre_beneficiario': 'Matin Tamizi', 
'tipo_cuenta_beneficiario': 40, 
'cuenta_beneficiario': '646180157029907065', 
'rfc_curp_beneficiario': 'No capturado.', 
'concepto_pago': 'Test2', 
'referencia_numerica': 181006, 
'empresa': 'TAMIZI', 
}
```

#### Enviar una orden

Si el cliente quiere realizar una transferencia, entonces el backend debe
colocar la tarea en RabbitMQ: 

```python
from celery import Celery

order = dict(
            concepto_pago='PRUEBA',
            institucion_ordenante='646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='072',
            monto=1020,
            nombre_beneficiario='Ricardo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            speid_id='SOME_RANDOM_ID',
            version=2
        )
app = Celery('speid')
app.send_task('speid.tasks.orders', kwargs={'order_val': order})
```

Estos son los campos obligatorios a incluir en la orden:

```python
{
    "concepto_pago": "Concepto"
    "institucion_ordenante": "Código del banco en SPEI",
    "cuenta_beneficiario": "CLABE del beneficiario",
    "institucion_beneficiaria": "Código del banco en SPEI",
    "monto": 120, # Cantidad en centavos
    "nombre_beneficiario": "Nombre",
    "nombre_ordenante": "Nombre",
    "cuenta_ordenante": "CLABE del ordenante",
    "rfc_curp_ordenante": "RFC",
    "version": 2 # Actualmente solo es soportada la versión 2
}
```

Campos opcionales:

```python
{
    "speid_id": "ID generado por el backend para identificar la orden",
    "empresa": "Default: Aquella que fue ingresada en las credenciales de STP",
    "folio_origen": "",
    "clave_rastreo": "Default: CR{TIME}",
    "tipo_pago": 1, # Default: 1
    "tipo_cuenta_ordenante": "",
    "tipo_cuenta_beneficiario": 40, # Default: 40
    "rfc_curp_beneficiario": "Default: ND",
    "email_beneficiario": "",
    "tipo_cuenta_beneficiario2": "",
    "nombre_beneficiario2": "",
    "cuenta_beneficiario2": "",
    "rfc_curpBeneficiario2": "",
    "concepto_pago2": "",
    "clave_cat_usuario1": "",
    "clave_cat_usuario2": "",
    "clave_pago": "",
    "referencia_cobranza": "",
    "referencia_numerica": 0, # Default: Número aleatorio
    "tipo_operacion": "",
    "topologia": "Default: T",
    "usuario": "",
    "medio_entrega": 3, # Default: 3
    "prioridad": 1, #Default: 1
    "iva": "",
}
```

Al momento de agregar la tarea de Celery, está es ejecutada por el Daemon
y se genera una nueva transacción con su correspondiente evento,
posteriormente se envía la orden al proveedor (STP) y el resultado se almacena
en un nuevo evento y se notifica al backend haciendo un PATCH al endpoint 
definido en la variable de ambiente `CALLBACK_URL` con el ID del request en la URL:

```python
{
'speid_id': 'SOME_ID',
'orden_id': 'orden_id',
'estado': 'submitted'
}
```

Cuando STP responde con el resultado de la operación, se recibe en el
servicio `/orden_events` el cual busca la transacción por el ID de la orden y
almacena un nuevo Evento. Posteriormente se notifica al backend haciendo un PATCH al 
endpoint definido en la variable de ambiente `CALLBACK_URL` con el ID del request en la 
URL.

El estado en el que puede responder STP para una transferencia son los siguientes:
1. `LIQUIDACION`: La transferencia fue exitosa.
2. `DEVOLUCION`: No fue posible realizar la transferencia. Este caso aplica 
para transferencias con destino a Instituciones participantes directos de SPEI.
3. `CANCELACION`: No fue posible realizar la transferencia. Este caso aplica 
para transferencias con destino a Instituciones que en su CLABE tengan el prefijo **646**, es decir, clientes de STP.

Cabe aclarar que en `speid` el estado `LIQUIDACION` mapea a `succeeded`, mientras que 
`DEVOLUCION` y `CANCELACION` mapean a `failed` para retornarse al backend.

Este es el cuerpo del mensaje en RabbitMQ:

````python
{
'orden_id': 'orden_id', 
'estado': 'success',    # Opciones [success, failed] 
'speid_id': 'SOME_ID'
}
````
En caso de querer realizar el callback al backend mediante queue se debe 
establecer las siguientes variables de entorno
```
SEND_TRANSACTION_TASK=ruta_de_la_tarea_transacciones de entrada``

SEND_STATUS_TRANSACTION_TASK=ruta_de_la_tarea_para_el_status``

CALLBACK_QUEUE_ACTIVE=true

```
___
Hecho con ❤️ en [Cuenca](https://cuenca.com/)