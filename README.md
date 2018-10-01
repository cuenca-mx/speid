## SPEI Daemon 

Envía y recibe órdenes SPEI. Utilizando RabbitMQ y Postgress para almacenar 
los datos.

**Requerimientos**

- Python v3 o superior.
- Postgres
- RabbitMQ

**Instalación**

Primero hay que declarar las variables de ambiente que se encuentran en
env.template.

Ejecutar la migración de base de datos:

```
flask docker create_db
flask db upgrade
flask docker drop_db
```


Se puede usar el archivo docker-compose como:

```
docker-compose up
```

**Test**

Para ejecutar los test utlizando el archivo Makefile

```
$ make test
```

**Uso básico**

Cuando se recibe una nueva orden SPEI, se hace una llamada al
servicio /ordenes. Se crea una transacción en la tabla transactions
y se asocia un evento tipo "create" a la tabla Events. Posteriormente
se guarda la orden en RabbitMQ para ser utilizado por el backend.
El servicio aguarda 15 segundos a obtener una respuesta la cual es 
almacenada en un nuevo Evento asociado a la Transacción y se devuelve la
respuesta.

Si el cliente quiere realizar una transferencia, entonces el backend debe
colocar la tarea en RabbitMQ como una orden de Celery: 

``` Python
from stpmex.types import Institucion

order = dict(
            conceptoPago='PRUEBA',
            institucionOperante=Institucion.STP.value,
            cuentaBeneficiario='646180157000000004',
            institucionContraparte=Institucion.BANORTE_IXE.value,
            monto=1.2,
            nombreBeneficiario='Ricardo Sánchez',
            nombreOrdenante='BANCO',
            cuentaOrdenante='072691004495711499',
            rfcCurpOrdenante='ND'
        )
app = Celery('stp_client')
app.config_from_object('speid.daemon.celeryconfig')
app.send_task('speid.daemon.tasks.send_order',
              kwargs={'order_dict': order})
```

Se puede utilizar el archivo de configuración o hacer una configuración
básica desde el backend para no tener dependencias.

Al momento de agregar la tarea de Celery, está es ejecutada por el Daemon
y se genera una nueva transacción con su correspondiente evento,
posteriormente se envía la orden al proveedor (STP) y el resultado se almacena
en un nuevo evento.

Cuando STP responde con el resultado de la operación, se recibe en el
servicio /orden_events el cual busca la transacción por el ID de la orden y
almacena un nuevo Evento. Posteriormente se envía a RabbitMQ para ser
procesado por el Backend.