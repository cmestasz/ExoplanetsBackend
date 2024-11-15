<div align="center">
<table>
    <thead>
        <tr>
            <td style="width:25%; text-align:center;"><img src="/img/epis.png" alt="EPIS" style="width:80%; height:auto"/></td>
            <td style="text-align:center;">
                <span><b>UNIVERSIDAD NACIONAL DE SAN AGUSTIN</b></span><br />
                <span><b>FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS</b></span><br />
                <span><b>DEPARTAMENTO ACADÉMICO DE INGENIERÍA DE SISTEMAS E INFORMÁTICA</b></span><br />
                <span><b>ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS</b></span>
            </td>
            <td style="width:25%; text-align:center;"><img src="/img/abet.png" alt="ABET" style="width:80%; height:auto"/></td>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td colspan="3"><span><b>Curso</b></span>: Interacción Humano Computador</td>
        </tr>
        <tr>
            <td colspan="3"><span><b>Fecha</b></span>: 20/09/2024</td>
        </tr>
    </tbody>
</table>
</div>
<div align="center" style="margin-top: 10px;">
    <img src="/img/unsa.png" alt="UNSA" width="450px" height="150px">
    <h1 style="font-weight:bold; font-size: 2em;">Exoplanets</h1>
</div>

Exoplanets es una aplicación interactiva para poder visualizar exoplanetas y las estrellas que los rodean usando la base de datos del [Archivo de Exoplanetas de la Nasa](https://exoplanetarchive.ipac.caltech.edu/) y la [Base de Datos de GAIA](https://www.cosmos.esa.int/web/gaia/data-release-3)

Además, permite interactuar con la aplicación mediante el uso de gestos, los que son reconocidos y procesados utilizando [OpenCV](https://opencv.org/) y [Mediapipe](https://developers.google.com/mediapipe).

El enfoque busca crear una aplicación que permita a estudiantes aprender más sobre los exoplanetas esparcidos en el universo y interactuar con estos de forma dinámica.

## Estado del Proyecto

🚧 **En Desarrollo** 🚧

El proyecto se encuentra en fase de desarrollo.

## Características (Esperadas) Principales

-   Seleccionar un exoplaneta y generar un mapa 3D de estrellas usando como referencia la posición del exoplaneta.
-   Generar una visualización interactiva que permita usar gestos para visualizar el espacio.
-   Exportar imágenes de alta calidad de los exoplanetas visibles desde esa posición.
-   Nombrar constelaciones y poder acceder a estas por su nombre

## Tecnologías Utilizadas

-   Simulador: Unity + React
-   Backend: FastAPI + OpenCV + Mediapipe
-   Despliegue: Aplicación de escritorio.

## Instrucciones de uso

🚧 **En Desarrollo** 🚧

## Requisitos para instalación

-   Unity 2022.3.37f1
-   Python 3.12.3
-   Node 22.11.0

## Instalación y Configuración (Desarrollo)

1.  Clonar el [Repositorio de Frontend](https://github.com/cmestasz/Exoplanets).
2.  Clonar el [Repositorio de Backend](https://github.com/cmestasz/ExoplanetsBackend).

### Python

1.  Crear un entorno virtual de Python 3.12.3 en la carpeta Backend/ del Repositorio de Backend instalando los requerimientos en el archivo requirements.txt.
2.  Ejecutar el servidor con:

```bash
fastapi dev main.py
```

3.  En caso no se pueda realizar la conexión con el servidor desde Unity, modificar la variable API_URL en Unity/Exoplanets/Assets/Scripts/APIConnector.cs para que encaje con el puerto del servidor iniciado por FastAPI.

### Node

1.  Instalar las dependencias del servidor de React contenidas en la carpeta Unity/Exoplanets/react con:

```bash
# usando npm
npm install
# usando pnpm
pnpm install
```

2.  Ejecutar el servidor con:

```bash
# usando npm
npm start
# usando pnpm
pnpm start
```

3.  En caso no se pueda realizar la conexión con el servidor desde Unity, modificar el atributo URL del objeto "React Canvas" en la escena a ejecutar para que encaje con el puerto del servidor iniciado por Node.

### Unity

1.  Abrir la carpeta Unity/Exoplanets/ con Unity Hub y vincularlo a un proyecto de Unity 2022.3.37f1.
2.  Iniciar los servidores de Node y Python antes de ejecutar el proyecto.
3.  Abrir el editor y ejecutar el proyecto.

## Demo en Vivo

🚧 **En Desarrollo** 🚧

## Autores

-   Carbajal Gonzales, Diego Alejandro
-   Mestas Zegarra, Christian Raul
-   Quispe Condori, Alvaro Raul
-   Sequeiros Condori, Luis Gustavo
-   Valdivia Segovia, Ryan Fabian

## Licencia

El proyecto se encuentra bajo los términos de la [Licencia MIT](/LICENSE)
