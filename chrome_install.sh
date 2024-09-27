#!/bin/bash

if ! command -v chromium-browser &> /dev/null
then
    echo "Installing Chromium"

    apt update
    apt install -y chromium-browser

    echo "Chromium installed successfully"
else
    echo "Chromium already installed"
fi