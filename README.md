# Dashboard de Gestión de Inscripciones Académicas

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)

Este proyecto es un dashboard interactivo desarrollado con Streamlit para gestionar y visualizar datos de inscripciones académicas. Proporciona métricas clave, gráficos de análisis y herramientas administrativas para el seguimiento de campañas de ventas educativas.

## Características principales

- 🔐 Autenticación segura de usuarios con roles y permisos
- 📊 Visualización de métricas clave en tiempo real
- 📈 Gráficos interactivos para análisis de datos
- ✏️ Formulario para agregar nuevos registros
- 📥 Exportación de datos en formato CSV
- 👥 Gestión de diferentes niveles académicos y ciclos escolares

## Estructura de archivos

```
.
├── venv/                   # Entorno virtual de Python
├── .gitignore              # Archivo para ignorar carpetas y archivos sensibles
├── app.py                  # Aplicación principal de Streamlit
├── config.yaml             # Configuración de usuarios y autenticación
├── datos.csv               # Base de datos de inscripciones (no incluido en repositorio)
├── Generar_hash.ipynb      # Notebook para generar hashes de contraseñas
└── requirements.txt        # Dependencias de Python
```

## Requisitos previos

- Python 3.8+
- Pip (gestor de paquetes de Python)

## Instalación y configuración

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/dashboard-inscripciones.git
   cd dashboard-inscripciones
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar usuarios:
   - Editar `config.yaml` con tus usuarios y permisos
   - Usar `Generar_hash.ipynb` para crear hashes seguros de contraseñas

5. Preparar datos iniciales:
   - Crear un archivo `datos.csv` con la estructura de datos necesaria

## Uso

Iniciar la aplicación:
```bash
streamlit run app.py
```

La aplicación estará disponible en:
```
http://localhost:8501
```

### Credenciales de ejemplo

| Usuario    | Contraseña      | Permisos                     |
|------------|-----------------|------------------------------|
| juanito    | abcdf123#$%      | Todos los permisos           |
| petronila   | passworD1/#    | Todos los permisos           |
| jaimico    | usuario123$     | Solo visualización           |

## Características de seguridad

- 🔐 Autenticación con hash bcrypt
- 🔑 Gestión de permisos por usuario
- 🛡️ Protección de archivos sensibles (config.yaml, datos.csv)
- 🔒 Acceso restringido a funciones administrativas

## Personalización

Puedes modificar los siguientes aspectos del dashboard:

1. **Niveles académicos**: Editar el diccionario `subniveles` en app.py
2. **Ciclos escolares**: Modificar el diccionario `ciclos` en app.py
3. **Permisos de usuario**: Actualizar `config.yaml`
4. **Métricas**: Ajustar las fórmulas en la sección de métricas principales

## Capturas de pantalla

![Dashboard](https://via.placeholder.com/800x400?text=Captura+del+Dashboard)
*Vista general del dashboard con métricas y gráficos*

![Formulario](https://via.placeholder.com/600x400?text=Formulario+de+Registro)
*Formulario para agregar nuevos registros*

## Contribución

Las contribuciones son bienvenidas. Por favor:

1. Haz un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

**Nota**: Por seguridad, nunca subas archivos sensibles como `config.yaml` o `datos.csv` a repositorios públicos.