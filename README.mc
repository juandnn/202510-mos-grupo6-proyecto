# Optimización de Rutas de Vehículos Problema B
Esteban Benavides - 202220429, Juan Pablo Castro - 202222086, Juan Diego Niebles - 202221193

## Expliación de repositorio:

Este repositorio es la entrega 2 del proyecto, donde ** se entrega el caso 1 completo, y el caso 2 y 3 parcialmente implementados. ** 
El repositorio cuenta con los siguientes elementos:

- datos/: es la carpeta en la cual se encuentran todos los datos para los 3 casos, es importante que al correr el caso 1 está carpeta tenga el mismo nombre y ubicación relativa.
- base_case_verification.py: es el programa para verificar el caso base.
- codigo_caso_1.ipynb: implementación del caso 1 completa
- codigo_caso_2.ipynb: implementación del caso 2 parcial
- codigo_caso_3.ipynb: implementación del caso 3 parcial
- distance_cache.json: cache de las distancias dadas por la API usada para calcularlas. Está para mejorar el rendimiento del programa.
- Correcciones_Modelo.pdf: Mismo documento de la entrega 1 con las correcciones hechas después de la retroalimentación. Lo amarillo es lo que estaba antes y lo verde es la corrección.
- README.mc: Este archivo
- solution.csv: Exportación de la solución encontrada en el caso 1

## Instrucciones para correr el código:

Para el caso 1, es un Jupyter Notebook, el cual se espera que corra en el environment de pyomo dado para este curso. Antes de correr el notebook completo es importante tener Gurobi instalado. Este es el solver que utilizamos. Los siguientes comandos deberian funcionar:
grbgetkey 77d88db4-9b5b-4bfd-b4ca-14f636d577f7
pip install gurobipy
o
conda install gurobi
En caso de que no funcione, es posible que se tenga que conseguir una licencia.
Esta es la guia de instalación: https://support.gurobi.com/hc/en-us/articles/14799677517585-Getting-Started-with-Gurobi-Optimizer

Después de instalar gurobi, el notebook se deberia poder correr completo sin problemas.
