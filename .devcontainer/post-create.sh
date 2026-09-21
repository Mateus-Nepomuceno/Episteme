#!/bin/bash

echo "Configurando o ambiente de desenvolvimento..."

pipx install poetry==2.4.3
pipx inject poetry poethepoet[poetry_plugin]
poetry config virtualenvs.in-project true
