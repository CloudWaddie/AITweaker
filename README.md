# AI Leaks Tweaker

A desktop application to intercept and modify network requests for AI web applications, allowing for real-time feature flag manipulation.

## Features

- **Profile Management**: Create, switch, import, and export different configuration profiles.
- **Gemini Tweaking**: Enable, disable, and add integer-based feature flags for Google's Gemini.
- **Copilot Tweaking**: Enable, disable, and add string-based feature flags for Microsoft's Copilot, and toggle the `allowBeta` setting.
- **Live Proxy Control**: Start and stop the `mitmproxy` backend directly from the UI.
- **Live Logging**: View logs from the proxy in real-time.

## Getting Started

### Prerequisites

- Python 3.8+
- `pip` (Python package installer)
- pipx install mitmproxy
### Installation

1.  **Clone the repository or download the source.**

2.  **Run the setup script for your operating system:**

    -   **Windows:**
        ```batch
        scripts\setup.bat
        ```

    -   **macOS/Linux:**
        ```sh
        bash scripts/setup.sh
        ```

## Usage

### 1. Running the Application

-   **Windows:**
    ```batch
    run.bat
    ```

-   **macOS/Linux:**
    ```sh
    ./run.sh
    ```

### 2. Setting up the Proxy

For the tool to intercept HTTPS traffic, you must set up the `mitmproxy` backend and install its CA certificate.

1.  **Launch the Tweaker GUI** using the command above.

2.  **Start the Proxy**: In the "Proxy" tab of the application, click the "Start Proxy" button. This will launch `mitmproxy` in the background on port 8000.

3.  **Install the CA Certificate**: `mitmproxy` requires you to install a custom root certificate to decrypt and modify HTTPS traffic.
    - **Easy Method**: While the proxy is running (step 2), click the **Open mitm.it to Get CA Certificate** button in the Proxy tab. This will open a special page in your browser with download links and instructions for your specific device.
    - **Manual Method**: If the button doesn't work, you can find the certificate file at `~/.mitmproxy/mitmproxy-ca-cert.pem` (on Windows, this is typically `C:\Users\YourUsername\.mitmproxy\mitmproxy-ca-cert.pem`).
    - **Installation**: Once you have the certificate (either from `mitm.it` or the file), follow the installation steps for your OS. On Windows, double-click the file, choose "Install Certificate...", select "Current User", then "Place all certificates in the following store", and browse to the **Trusted Root Certification Authorities** store.

4.  **Configure Your System Proxy**:
    - Set your operating system's HTTP and HTTPS proxy to point to `127.0.0.1` on port `8000`.
    - **On Windows**: Go to Settings > Network & Internet > Proxy. Turn on "Use a proxy server" and set the address to `127.0.0.1` and port to `8000`.
    - **On macOS**: Go to System Preferences > Network > Advanced > Proxies. Check both "Web Proxy (HTTP)" and "Secure Web Proxy (HTTPS)" and set the server to `127.0.0.1` and port to `8000` for both.

    **Alternative: Using a Browser Extension (Recommended)**

    For more granular control, you can use a browser extension like **FoxyProxy** to route only your browser's traffic through the tweaker, leaving the rest of your system's network traffic unaffected.

    1.  Install FoxyProxy Standard/Basic for your browser (e.g., Firefox, Chrome).
    2.  Open the FoxyProxy options.
    3.  Click "Add New Proxy".
    4.  Configure it with the Host/IP Address `127.0.0.1` and Port `8000`.
    5.  You can then enable this proxy from the extension's icon in your browser's toolbar whenever you want to use the tweaker.



## Support the Project

If you find this tool useful, please consider supporting its development! The donation button on my GitHub profile uses NOWPayments.

[Please Donate via GitHub](https://github.com/cloudwaddie)