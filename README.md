## apiProxy

### Introducción

Aplicación destinada al uso de proxy de otras apis, en este caso está apuntanndo a dos endpoints diferentes

- api.mercadolibre.com
- fakeapi.com

Al realizar un request a `localhost:8081/meli` o `localhost:8081/fakeApi`podemos traer el contenido de las apis principales a traves de un request (sin redirect ni caching)


### Cómo ejecutar

Desde el directorio raíz ejecutar
```
docker compose up -d
```

### Cómo funciona

#### Api
El servicio está creado en Flask, usando Gunicorn como servidor WSGI y se ejecuta a través de docker (Hay un docker-compose que ya se encarga de crear todos los recursos necesarios para su funcionamiento)


#### Backend (Redis)

Como backend del servicio se está usando redis, el cual está separado en 3 dbs diferentes

- db0: logs (Guarda todos los logs de request/response que tiene la api)
- db1: rules (Guarda las reglas que se usan para el filtro de accesos por ip y/o path)
- db2: limits (Crea keys temporales con TTLs definidos que se encargan de contar los request restantes permitidos en N segundos)

#### Load Balancer (Traeffik)

Se configuró Traeffik como load balancer en docker-compose para poder escalar el contenedor de API y maximizar la cantidad de requests permitidos, es una muestra conceptual de que el servicio puede escalarse en K8s u otras plataformas.

- Traeffik dashboard: localhost:8080
- Traeffik balancer: localhost:8081

### Load Tests

Podemos realizar una prueba de carga y respuesta con el siguiente comando, apuntando a la API de mercadolibre para constatar los tiempos de respuesta y la cantidad de requests funcionales (Necesario contar con apache2-utils instalado)

`ab -n 500 -c 50 localhost:8081/meli/categories/MLA97994`

- -n: se refiere a la cantidad de llamadas totales
- -c: se refiere a la concurrencia de llamadas

### Security Tests

En el archivo ./src/configs/limiter.py podemos ver que hay un listado de reglas a constatar para bloquear los accesos, las mismas se configuran de la siguientes:

#### == Este es el orden establecido de chequeo ==
- "IP;Path": "Requests/Period"
- "Path": "Requests/Period"
- "IP": "Requests/Period"

Donde "period" puede ser alguna de las siguientes opciones: second/minute/hour/day

Ejemplos:

- "192.168.0.1;/categories": "5/day" -> En este caso se permiten hasta 5 requests por día desde la ip 192.168.0.1 hacia el path /categories
- "/sites": "10/hour" -> En este caso se permiten hasta 10 requests por hora hacia el path /sites
- "192.168.0.1": "15/minute" -> En este caso se permiten hasta 15 requests por minuto desde la ip 192.168.0.1

Las reglas se usan con todos los filtros en su conjunto, por lo que se pueden dar los siguientes casos:

- El request proviene de la ip 192.168.0.1 al path /sites -> La regla tomada será la de path ya que es la regla con más peso.

- El request proviene de la ip 192.168.0.1 al path /categories -> La regla tomada será la de IP;path ya que es la que matchea con ambos criterios.

- El request proviene de la ip 192.168.0.1 al path / -> La regla tomada será la de IP ya que es la única regla que matchea al no tener ninguna regla con path "/" definido.

#### Check rules

Dentro del contenedor de api-redis, ejecutamos redis-cli y con los siguientes comandos podemos revisar las reglas creadas y los permisos que tiene cada regla definidos

```
127.0.0.1:6379[1]> select 1
OK
127.0.0.1:6379[1]> keys *
1) "172.19.0.2"
2) "172.19.0.2;/categories"
3) "152.152.152.152;/items"
4) "172.19.0.2;/sites"
5) "/categories"
127.0.0.1:6379[1]> get 172.19.0.2
"15/minute"
```

Las reglas se reinician al crear cada contenedor

#### Check limits

Dentro del contenedor de api-redis, ejecutamos redis-cli y con los siguientes comandos podemos revisar los límites creados y los requests restantes así como el TTL de cada regla creada.
(El TTL del límite es expresado en segundos)

```
127.0.0.1:6379[1]> select 2
OK
127.0.0.1:6379[2]> keys *
1) "172.19.0.2;/categories"
127.0.0.1:6379[2]> get 172.19.0.2;/categories
"0"
127.0.0.1:6379[2]> TTL 172.19.0.2;/categories
(integer) 54449
127.0.0.1:6379[2]> 
```

En este caso, podemos ver que si desde la ip 172.9.0.2 intento ingresar al path /categories, no puedo ya que no tengo requests permitidos, por lo que recibiré el siguiente mensaje

```
π apiProxy main ✗ ❯ curl -XGET localhost:8081/meli/categories/MLA97994
{"error":"404 Not Found: {'Connection limit excedeed'}"}
```

### Logging

#### Check logs (Redis)

Dentro del contenedor de api-redis, ejecutamos redis-cli y con los siguientes comandos podemos revisar los logs de la aplicación

```
127.0.0.1:6379> select 0
OK
127.0.0.1:6379> keys *
1) "logs:meli:11-05-2024"
```

Para poder ver los logs, es necesario ejecutar el comando LRANGE ya que es una lista de redis.

```
127.0.0.1:6379> lrange logs:meli:11-05-2024 0 -1
```

#### Check logs (Api)

La api posee un endpoint específico para revisar los logs.

- localhost:8081/logs

Una vez dentro, vamos a ver la misma estructura que en redis

- logs:meli:11-05-2024
- logs:fakeApi:11-05-2024

Para poder ingresar, sólo tenemos que ir al path con el nombre de la aplicación/día

- localhost:8081/logs/meli/11-05-2024

### Cómo escalar

Una vez creada la imagen con el nombre apiProxy, se puede modificar el docker-compose sacándole las lineas de build y descomentando la linea de image, quedando de la siguiente forma:

```
version: '3.7'

services:
  api-proxy:
    image: apiproxy
    #build:
    #    context: .
    #    dockerfile: Dockerfile
```

Una vez realizado este cambio, podemos proceder a ejecutar el comando (Donde 15 es el número de contenedores deseados)

```
docker compose scale api-proxy=15
```

Y de esta manera vemos que los contenedores de apiProxy nuevos van a crearse y a traves de los labels definidos en docker van a registrarse automáticamente en Traeffik para así empezar a balancear los requests