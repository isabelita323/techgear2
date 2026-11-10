💄 TechGear Beauty
TechGear Beauty es una tienda web de maquillaje y productos de belleza que permite a los usuarios explorar un catálogo de productos, consultar sus características, gestionar sus cuentas y realizar pedidos de manera sencilla.

El proyecto está desarrollado con una arquitectura basada en Django, FastAPI y MongoDB, separando la interfaz web de los servicios encargados de gestionar la información.

📌 Tabla de contenido
Descripción del proyecto
Características principales
Tecnologías utilizadas
Arquitectura del proyecto
Funcionalidades
Instalación y configuración
Ejecución del proyecto
Documentación de la API
Roles de usuario
Autor
📝 Descripción del proyecto
TechGear Beauty es una plataforma de comercio electrónico enfocada en la venta de maquillaje y productos de belleza.

Su objetivo es ofrecer una experiencia de compra intuitiva, permitiendo a los clientes consultar productos, conocer su disponibilidad, realizar pedidos y revisar su historial de compras.

Además, cuenta con un panel de administración que facilita la gestión del catálogo y una API REST que centraliza las operaciones relacionadas con productos, usuarios y pedidos.

✨ Características principales
🛍️ Catálogo de productos: visualización de productos con nombre, descripción, categoría, precio, existencias e imagen.
🔎 Filtros por categoría: permite encontrar productos según su clasificación.
📦 Control de inventario: identifica productos disponibles y agotados.
👤 Gestión de usuarios: registro e inicio de sesión.
🛒 Carrito de compra por sesión: permite agregar productos y cantidades, actualizar o quitar artículos antes de confirmar.
🛒 Gestión de pedidos: confirma pedidos con la cuenta autenticada y valida el stock al realizar la compra.
💰 Cálculo de totales: calcula automáticamente el valor de cada pedido.
📋 Historial de compras: permite consultar los pedidos realizados.
⚙️ Panel de administración: permite crear, editar y eliminar productos.
🔄 Actualización de existencias: descuenta las unidades correspondientes al realizar pedidos.
🧰 Tecnologías utilizadas

Tecnología	Descripción
Python	Lenguaje principal del backend.
Django	Desarrollo de páginas web, vistas y navegación.
FastAPI	Desarrollo de servicios y API REST.
MongoDB	Base de datos NoSQL para almacenar la información.
HTML	Estructura de las páginas web.
CSS	Diseño y estilos de la interfaz.
JavaScript	Interactividad de la página web.
🏗️ Arquitectura del proyecto
El sistema utiliza una arquitectura dividida en tres componentes principales:

1. Django – Aplicación web
Se encarga de la interfaz gráfica y la interacción con los usuarios.

Responsabilidades:

Mostrar el catálogo de productos.
Gestionar el registro e inicio de sesión.
Permitir la navegación por la tienda.
Mostrar los pedidos de cada cliente.
Proporcionar el panel de administración.
2. FastAPI – Servicios REST
Se encarga de procesar las solicitudes y gestionar las operaciones del sistema.

Responsabilidades:

Consultar productos.
Registrar, actualizar y eliminar productos.
Gestionar usuarios.
Crear y consultar pedidos.
Actualizar estados de los pedidos.
Controlar las existencias.
3. MongoDB – Base de datos
Se utiliza para almacenar la información de la aplicación.

Colecciones principales:

productos: información del catálogo.
usuarios: información de las cuentas.
pedidos: artículos, cantidades, totales y estados de los pedidos.
⚙️ Funcionalidades
🛍️ Catálogo de productos
Cada producto contiene la siguiente información:

Nombre.
Descripción.
Categoría.
Precio.
Existencias.
Imagen.
Los clientes pueden consultar el catálogo, filtrar por categorías y verificar la disponibilidad de los productos.

👤 Cuentas de usuario
El sistema permite:

Registrar nuevas cuentas.
Iniciar sesión.
Asociar los pedidos a cada usuario.
Consultar el historial de compras mediante la opción Ver mis pedidos.
🛒 Gestión de pedidos
Los clientes pueden agregar productos al carrito desde cada tarjeta del catálogo, ajustar cantidades y revisar el total antes de confirmar.

Para finalizar la compra, inicia sesión y proporciona una dirección de envío. El carrito se conserva durante el inicio de sesión; la API vuelve a comprobar el inventario antes de registrar el pedido.

El sistema se encarga de:

Registrar los productos seleccionados.
Calcular el total del pedido.
Actualizar las existencias disponibles.
Asociar cada pedido con su respectivo cliente.
Gestionar el estado de los pedidos desde la API.
🔐 Panel de administración
Los usuarios con permisos de administrador pueden gestionar el catálogo de productos.

Funciones disponibles:

Agregar nuevos productos.
Editar información existente.
Eliminar productos.
Administrar precios y existencias.
🚀 Instalación y configuración
Requisitos previos
Antes de ejecutar el proyecto, asegúrate de tener instalado:

Python 3.10 o superior.
MongoDB.
Git.
pip (gestor de paquetes de Python).
1. Clonar el repositorio

bash
git clone URL_DEL_REPOSITORIO
Ingresar a la carpeta del proyecto:


bash
cd TechGear-Beauty
2. Crear un entorno virtual para cada servicio

Desde la carpeta raíz del proyecto:

Windows:

```powershell
python -m venv techgear_api\.venv
python -m venv techgear_web\.venv
```

Linux / macOS:

```bash
python3 -m venv techgear_api/.venv
python3 -m venv techgear_web/.venv
```

3. Instalar las dependencias

Windows:

```powershell
techgear_api\.venv\Scripts\python -m pip install -r techgear_api\requirements.txt
techgear_web\.venv\Scripts\python -m pip install -r techgear_web\requirements.txt
```

Linux / macOS:

```bash
techgear_api/.venv/bin/python -m pip install -r techgear_api/requirements.txt
techgear_web/.venv/bin/python -m pip install -r techgear_web/requirements.txt
```
4. Configurar MongoDB
Verificar que MongoDB esté instalado y en funcionamiento.

Configurar la cadena de conexión en las variables de entorno o en el archivo de configuración correspondiente.

Ejemplo:


env
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=techgear_beauty
Nota: No subir credenciales, contraseñas ni archivos .env al repositorio.

▶️ Ejecución del proyecto
El proyecto utiliza dos servicios principales que deben ejecutarse de manera independiente.

Iniciar FastAPI
Desde la carpeta raíz del proyecto:

```powershell
cd techgear_api
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en:


text
http://127.0.0.1:8000
Iniciar Django
En otra terminal, desde la carpeta raíz del proyecto:

```powershell
cd techgear_web
.venv\Scripts\activate
python manage.py runserver 8001
```

La aplicación web estará disponible en:


text
http://127.0.0.1:8001
Importante: Si ambos servicios se ejecutan en el mismo equipo, deben utilizar puertos diferentes. Por ejemplo, FastAPI en el puerto 8000 y Django en el 8001.

### Configuración local e imágenes de productos

Crear `techgear_api/.env` con `MONGODB_URI`, `MONGODB_DB`, `API_KEY` y `JWT_SECRET`. Crear `techgear_web/.env` con `API_URL`, `API_KEY`, `SECRET_KEY` y `DEBUG=True`. La `API_KEY` debe tener el mismo valor en ambos archivos. No guardar secretos en el repositorio.

Al crear un producto desde la web, subir una imagen JPG, PNG o WebP de hasta 4 MB. En desarrollo las imágenes se guardan en `techgear_web/media/productos/`; en producción se guardan en un almacén público de Vercel Blob y MongoDB conserva la URL permanente. El límite de 4 MB deja espacio para el multipart dentro del límite de solicitud de Vercel. Las cuatro imágenes actuales del catálogo se incluyen como archivos estáticos del proyecto, por lo que también se sirven desde el CDN de Vercel.

La creación de productos desde el formulario requiere iniciar sesión con una cuenta administradora.

En el catálogo, una cuenta administradora puede marcar uno o varios productos. "Editar seleccionado" se habilita con exactamente un producto; "Eliminar seleccionados" permite eliminar varios tras confirmar. El menú muestra el total de productos, incluso cuando se filtra por categoría.

Las fotos actuales del catálogo son fotografías reales obtenidas de Unsplash y guardadas localmente. Son imágenes de referencia; confirma que correspondan a la marca y presentación exactas de cada producto antes de usarlas para venderlo.

- [Maquillaje](https://images.unsplash.com/photo-1547887538-e3a2f32cb1cc)
- [Paleta y cosméticos](https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9)
- [Cuidado facial](https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8)
- [Perfume](https://images.unsplash.com/photo-1592945403244-b3fbafd7f539)
- [Licencia de Unsplash](https://unsplash.com/license)

### Despliegue en Vercel

La aplicación tiene dos servicios independientes. Importa el mismo repositorio en dos proyectos de Vercel y configura sus directorios raíz:

1. Proyecto web Django: `techgear_web`.
2. Proyecto API FastAPI: `techgear_api`.

Cada servicio incluye su propio `vercel.json`, `.python-version` y `requirements.txt`. En ambos proyectos configura las variables como **Production, Preview y Development** según corresponda. Usa Python 3.13, compatible con el runtime de Vercel.

En el proyecto API configura:

- `MONGODB_URI`: URI de MongoDB Atlas accesible desde internet; no uses `localhost`.
- `MONGODB_DB`: nombre de la base de datos, por ejemplo `techgear`.
- `API_KEY`: clave aleatoria compartida con el proyecto web.
- `JWT_SECRET`: secreto aleatorio independiente para firmar tokens.
- `JWT_EXPIRE_MINUTES`: opcional; por defecto `60`.

En el proyecto web configura:

- `DEBUG=False`.
- `SECRET_KEY`: clave Django aleatoria y privada.
- `API_URL`: URL HTTPS pública del proyecto API, por ejemplo `https://tu-api.vercel.app`.
- `API_KEY`: el mismo valor configurado en la API.
- `ALLOWED_HOSTS`: `.vercel.app` y cualquier dominio personalizado.
- `CSRF_TRUSTED_ORIGINS`: origen HTTPS de Vercel y el dominio personalizado, separados por comas.

En **Storage** del proyecto web crea un almacén Vercel Blob de acceso **público** y conéctalo al proyecto. Vercel proporcionará las credenciales de Blob al runtime. No agregues secretos ni archivos `.env` al repositorio. Usa `.env.example` de cada servicio como referencia; reemplaza todos los valores de ejemplo por valores reales en el panel de Vercel.

MongoDB Atlas debe tener habilitado el acceso de red para las funciones de Vercel y un usuario con permisos sobre la base de datos de la tienda. Los productos, usuarios y pedidos locales no se copian al crear el despliegue: importa los datos a Atlas antes de cambiar `MONGODB_URI`.

Los proyectos de Vercel deben enlazarse al repositorio y desplegarse después de configurar las variables y Blob. Comprueba `https://tu-api.vercel.app/health` (debe indicar MongoDB conectado), `https://tu-api.vercel.app/docs` y la página de catálogo. Los archivos que se suban después se guardarán en Blob; las fotos ya incluidas en el repositorio se sirven desde `/static/`.

📚 Documentación de la API
FastAPI proporciona documentación interactiva para consultar y probar los servicios disponibles.


Ruta	Descripción
/docs	Documentación interactiva con Swagger UI.
/health	Ruta para comprobar el estado del servicio.
Documentación Swagger:


text
http://127.0.0.1:8000/docs
Comprobación del servicio:


text
http://127.0.0.1:8000/health
👥 Roles de usuario
El sistema contempla dos tipos principales de usuarios:


Rol	Permisos
Cliente	Consultar productos, registrarse, iniciar sesión, realizar pedidos y consultar su historial.
Administrador	Gestionar el catálogo de productos y administrar la información correspondiente desde el panel de administración.
📁 Estructura general del proyecto
La estructura puede organizarse de la siguiente manera:


text
TechGear-Beauty/
│
├── django_app/
│   ├── templates/
│   ├── static/
│   ├── views.py
│   ├── urls.py
│   └── models.py
│
├── fastapi_app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   └── database/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
Nota: Esta es una estructura de referencia que puedes adaptar a la organización real de tus carpetas y archivos.

🎯 Objetivo del proyecto
Desarrollar una plataforma web de comercio electrónico que integre tecnologías modernas de desarrollo backend, permitiendo gestionar productos, usuarios, inventario y pedidos mediante una arquitectura que separa la aplicación web de los servicios API y la base de datos.

👨‍💻 Autor
Desarrollador: [Isabella zambrano]

Proyecto: TechGear Beauty

Tecnologías principales: Python, Django, FastAPI y MongoDB.

⭐ Si este proyecto te resulta interesante, no olvides darle una estrella al repositorio.
