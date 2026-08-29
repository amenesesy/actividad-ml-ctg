# Detección de anomalías y técnicas de agrupamiento sobre el conjunto de datos CTG

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/amenesesy/actividad-ml-ctg/blob/main/ML_Actividad_CTG.ipynb)

Actividad de la asignatura **Aprendizaje Automático** de la Maestría en
Inteligencia Artificial. El trabajo aplica el flujo completo de aprendizaje no
supervisado al conjunto de datos de cardiotocografía `CTG.csv`, que reúne 2 126
registros de monitoreo fetal descritos por 21 variables cuantitativas.

Autor: Abel Meneses Yaranga.

## Ejecución en Google Colab

Pulsando el distintivo de arriba el cuaderno se abre en Google Colab y puede
ejecutarse de principio a fin sin instalar nada. La primera celda detecta el
entorno, comprueba que estén las librerías necesarias, instala las que falten y
descarga `CTG.csv` desde este mismo repositorio. La ejecución completa tarda
alrededor de dos minutos y deja en el directorio de trabajo las quince figuras
y el archivo `resultados.json`.

El mismo cuaderno funciona sin cambios en una instalación local; en ese caso
basta con tener `CTG.csv` junto al archivo `.ipynb`, aunque si no está también
se descarga solo.

## Contenido del repositorio

`Actividad_ML_CTG_Meneses.pdf` es el informe final. Tiene 40 páginas, está
compuesto en Calibri 12 con interlineado 1,5 y contiene la narrativa completa,
todo el código Python comentado, las salidas que produce y las quince figuras
en formato APA. Reproduce la plantilla del enunciado: el encabezado de tres
columnas con la asignatura, los datos del alumno y la fecha, el pie con la
pestaña del número de página, y la paleta institucional construida sobre el
cian corporativo `#0098CD` y los grises `#333333` y `#777777`. Las figuras usan
esa misma paleta.

Las treinta y dos celdas de código se reproducen en el informe como captura del
cuaderno abierto en Google Colab, con el resaltado de sintaxis y el área de
salida tal como los presenta el entorno. En las trece celdas que dibujan una
figura la captura recoge el código y la salida de texto, y el gráfico va justo
después en formato APA con su número, su título y su nota: así se ve a un tamaño
legible y no aparece dos veces. La franja que ocupa cada gráfico dentro de su
captura está anotada en `recorte.py`, comprobada una a una sobre la imagen. Con
ese reparto, y con la narrativa sintetizada, el informe cabe en las 40 páginas
que fija el enunciado.

Colab encierra las salidas gráficas en un marco de mil píxeles de alto, de modo
que en las celdas 2.4 y 2.5 el final de la salida de texto quedaba fuera del
área visible. Las capturas de esas dos celdas se tomaron con ese marco ajustado
a la altura real del contenido, así que reproducen la salida completa.

`ML_Actividad_CTG.ipynb` es el cuaderno ya ejecutado, con 60 celdas de las
cuales 32 son de código, y conserva embebidas todas las salidas y los gráficos.
Las filas 2127 y 2128 del archivo original no son pacientes sino las filas de
resumen de la hoja de cálculo: reproducen, respectivamente, el mínimo y el
máximo de cada columna, y el cuaderno lo comprueba variable a variable.

`capturas/` contiene las treinta y dos capturas de celda tomadas del cuaderno en
Colab, y `capturas_recortadas/` las trece que el informe usa sin la franja del
gráfico.
`resultados.json` recoge los resultados numéricos que el cuaderno vuelca al
terminar y `figuras/` contiene las quince figuras en PNG a su resolución
original. `CTG.csv` es una copia local del conjunto de datos.

Los scripts `nb_base.py`, `nb_parte1.py` a `nb_parte4.py`, `build_notebook.py`,
`recorte.py` y `build_report.py` son la maquinaria que genera el cuaderno y el
informe.

## Cómo se regenera todo

```bash
python build_notebook.py
```

```bash
python -m jupyter nbconvert --to notebook --execute --inplace ML_Actividad_CTG.ipynb
```

```bash
python build_report.py
```

El script `build_notebook.py` ensambla el cuaderno a partir de los módulos
`nb_parte1.py` a `nb_parte4.py`, en los que cada celda se declara como una
cadena de texto y `nb_base.py` las serializa al formato nbformat v4. Por su
parte, `build_report.py` construye el PDF leyendo el cuaderno ya ejecutado, de
modo que ninguna cifra del informe se transcribe a mano y el documento no puede
desincronizarse del análisis. La semilla aleatoria está fijada en 42 en todo el
trabajo, de manera que la ejecución es reproducible.

## Estructura del análisis

Las secciones 1 y 2 cubren el diccionario de variables, los estadísticos
descriptivos, las frecuencias de las categóricas y la matriz de correlaciones.
La sección 3 diagnostica los valores faltantes, justifica la decisión que se
toma con ellos y la respalda con un experimento controlado de imputación. La
sección 4 selecciona las variables, depura las redundancias y estandariza las
escalas. La sección 5 aplica el Z-score, la regla de Tukey, la distancia de
Mahalanobis robusta, Isolation Forest y el factor local de atipicidad. La
sección 6 aplica K-Means, DBSCAN y el agrupamiento jerárquico aglomerativo, con
validación interna y externa. Las secciones 7 y 8 comparan las ventajas y
desventajas de cada modelo y recogen las conclusiones y las referencias.

## Resultados principales

Las 106 celdas faltantes del archivo se concentran en tres filas que resultaron
ser las filas de resumen de la hoja de cálculo original: una de mínimos y otra
que repite el máximo de cada columna. Se eliminan en lugar de imputarse. El
experimento controlado
muestra que, si los faltantes hubieran sido reales y dispersos, la mejor
estrategia habría sido la imputación por vecinos más cercanos, con un RMSE
normalizado de 0,224 frente al 0,382 de la media.

En detección de anomalías, Isolation Forest es el mejor método. Marcando el 5 %
de los registros, el 54,2 % de los señalados son casos patológicos frente a una
tasa base del 8,3 %, lo que supone un lift de 6,55 y un recall del 33 %.

En agrupamiento, K-Means con tres grupos alcanza un índice de Rand ajustado de
0,214 frente a la etiqueta `NSP` y recupera tres fenotipos clínicos
interpretables: un trazado tranquilizador con un 97,1 % de casos normales, un
grupo de vigilancia con un 31 % de sospechosos y un grupo comprometido con un
51,5 % de patológicos, que concentra el 60 % de todos los casos graves del
conjunto.

## Entorno

Python 3.14 con pandas 3.0, NumPy 2.3, scikit-learn 1.9, SciPy 1.18,
matplotlib 3.11, seaborn 0.13 y reportlab 5.0.
