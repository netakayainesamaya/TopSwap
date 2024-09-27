#!/bin/bash

if ! command -v chromium-browser &> /dev/null
then
    echo "Installing Chromium"
    apt-get update
    apt-get install -y chromium-browser
    echo "Chromium installed successfully"
else
    echo "Chromium already installed"
fi