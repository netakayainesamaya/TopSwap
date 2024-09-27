#!/bin/bash

if ! command -v chromium-browser &> /dev/null
then
    echo "Installing Chromium"

    sudo apt update
    sudo apt install -y chromium-browser

    echo "Chromium installed successfully"
else
    echo "Chromium already installed"
fi