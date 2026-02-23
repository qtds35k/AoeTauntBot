# AoeTauntBot Oracle Cloud Deployment Guide

This guide will walk you through setting up AoeTauntBot on your Oracle Cloud Always Free instance.

## Prerequisites

1.  **Oracle Cloud Account**: Sign up for an Oracle Cloud account and create an "Always Free" VM instance (Ampere A1 Compute is recommended as you get 4 cores and 24GB RAM).
2.  **SSH Access**: Ensure you have SSH access to your newly created instance.
3.  **Discord Bot Token**: Have your Discord Bot Token ready. You can get this from the Discord Developer Portal.

## Step-by-Step Deployment

1.  **Assign a Public IP Address (If missing during creation):**
    If the option to assign a public IPv4 address was grayed out during setup:
    1. Go to your Instance Details page.
    2. Scroll down on the left-hand menu and click **Attached VNICs**.
    3. Click on the name of your primary VNIC.
    4. At the top of the VNIC details, click the **IP administration** tab (next to Details).
    5. Click the **"..."** menu on the right side of the unassigned IP row and select **Edit**.
    6. Change the Public IP Type from "No public IP" to **"Ephemeral public IP"** and save.

2.  **SSH into your instance:**
    Connect to your Oracle Cloud VM using your preferred SSH client (e.g., PuTTY, Windows Terminal, or macOS/Linux terminal) using the Public IP you just assigned.

2.  **Install Git and Docker:**
    Run the following commands to install Git and the Docker ecosystem:
    ```bash
    sudo apt update
    sudo apt install git docker.io docker-compose-v2 -y
    sudo systemctl enable --now docker
    # Add your user to the docker group so you don't need sudo for docker commands
    sudo usermod -aG docker $USER
    # You will need to log out and log back in for the group change to take effect.
    ```

3.  **Clone the Repository:**
    Clone your bot's repository to the server:
    ```bash
    git clone https://github.com/qtds35k/AoeTauntBot.git
    cd AoeTauntBot
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file from the example or manually to store your Discord token:
    ```bash
    echo "DISCORD_TOKEN=your_actual_token_here" > .env
    ```
    *(Replace `your_actual_token_here` with your bot's token).*

5.  **Build and Run the Bot:**
    Use `docker compose` to build the image and start the container in the background (`-d` means detached mode).
    ```bash
    docker compose up -d --build
    ```

## Managing the Bot

*   **View Logs:** Check what the bot is printing to the console:
    ```bash
    docker logs aoetauntbot -f
    ```
*   **Stop the Bot:**
    ```bash
    docker compose down
    ```
*   **Update the Bot Code:** If you push new Python code to GitHub:
    ```bash
    git pull
    docker compose up -d --build
    ```
*   **Update Audio Files ONLY:** Because we setup a Volume Mount for the `bot/audio` folder, you don't need to rebuild the container if you just add a new `.ogg` file:
    ```bash
    git pull
    docker restart aoetauntbot
    ```

Your bot should now be online and ready to join voice channels!
