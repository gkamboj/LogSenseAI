#!/bin/bash
python -m pip install --upgrade pip
python -m pip install "generative-ai-hub-sdk[all]==1.2.2" --extra-index-url https://int.repositories.cloud.sap/artifactory/api/pypi/proxy-deploy-releases-hyperspace-pypi/simple
streamlit run app.py --server.port=8080